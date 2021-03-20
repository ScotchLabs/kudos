import itsdangerous, json, atexit, traceback, logging

from flask import redirect, render_template, url_for, abort, \
    flash, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm

from app_manager import app, db, ts, mail, DAY
from forms import SignupForm, LoginForm, UsernameForm, ResetPasswordForm, \
    ChangePasswordForm, NominationForm, VoteForm, BanForm, AdminForm, \
    NomIDForm, PhaseNomForm, PhaseVoteForm, PhaseStaticForm, SetPhaseForm, \
    ClearForm, RemoveNomForm
from models import User, Award, Nomination, State
from login_manager import login_manager
from dbutils import clear_noms, clear_votes

from werkzeug.exceptions import default_exceptions
from urllib.parse import urlparse, urljoin
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from logging.handlers import SMTPHandler
from io import StringIO

scheduler = BackgroundScheduler(timezone="US/Eastern")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", phase=phase())

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.lower(),
                    password=form.password.data)
        db.session.add(user)

        db.session.flush()

        if send_confirm_link(user.id, user.email):
            db.session.commit()
            flash("Account created! Please click the confirmation link sent "
                  "to %s" % user.email, "success")
            return redirect(url_for("index"))

    return render_template("signup.html", form=form)

@app.route("/confirm/<token>", methods=["GET"])
def confirm_email(token):
    try:
        userID, email = ts.loads(token, salt="email-confirm-key", max_age=DAY)
    except itsdangerous.SignatureExpired:
        return render_template("activate_expired.html", token=token)
    except:
        abort(404)

    user = User.query.filter_by(id=userID).first_or_404()

    if user.email != email:
        abort(404) # this shouldn't ever happen

    if user.email_confirmed == True:
        return render_template("already_confirmed.html")

    user.email_confirmed = True
    db.session.commit()
    flash("Email confirmed! Sign in!", "success")
    return redirect(url_for("signin"))

@app.route("/newlink/<token>", methods=["GET"])
def new_link(token):
    try:
        userID, email = ts.loads(token, salt="email-confirm-key") # ignore age
    except:
        abort(404)

    user = User.query.filter_by(id=userID).first_or_404()
    if user.email != email:
        abort(404) # this shouldn't ever happen
    if send_confirm_link(userID, email):
        flash("New confirmation link sent, check your email!", "success")
        return redirect(url_for("index"))
    else:
        # send them back to the expired confirm page
        return redirect(url_for("confirm_email", token=token))

@app.route("/resend", methods=["GET", "POST"])
def resend():
    form = UsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data.lower()).first_or_404()
        if user.email_confirmed == True:
            flash("Your email is already confirmed!", "error")
        elif send_confirm_link(user.id, user.email):
            flash("New confirmation link sent, check your email!", "success")
            return redirect(url_for("index"))
    return render_template("resend.html", form=form)

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        next_url = request.args.get("next")
        if not is_safe_url(next_url):
            abort(400)
        return redirect(next_url or url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data.lower()).first_or_404()
        if not user.email_confirmed:
            flash("Please click the confirmation link sent to your email first",
                  "error")
            return redirect(url_for("signin"))
        if user.is_correct_password(form.password.data):
            if user.banned:
                flash("Your account has been banned", "error")
                return redirect(url_for("signin"))
            login_user(user, remember=True)
            flash("Logged in successfully", "success")
            next_url = request.args.get("next")
            if not is_safe_url(next_url):
                abort(400)
            return redirect(next_url or url_for("index"))
        else:
            flash("Password incorrect, try again", "error")
    return render_template("signin.html", form=form)

@app.route("/signout", methods=["GET"])
def signout():
    if current_user.is_authenticated:
        logout_user()
        flash("Logged out", "success")
    return redirect(url_for("index"))

@app.route("/reset", methods=["GET", "POST"])
def reset():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = UsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data.lower()).first_or_404()
        subject = "Password reset requested"
        token = ts.dumps(user.username, salt="recover-key")
        recover_url = url_for("reset_with_token", token=token, _external=True)
        html = render_template("email/recover.html", recover_url=recover_url)
        if send_email(user.email, subject, html):
            flash("A password reset link has sent to your email address", "success")
            return redirect(url_for("index"))
    return render_template("reset.html", form=form)

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    try:
        username = ts.loads(token, salt="recover-key", max_age=DAY)
    except itsdangerous.SignatureExpired:
        return render_template("recover_expired.html")
    except:
        abort(404)

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        user.password = form.password.data
        db.session.commit()
        flash("Password reset successfully! Sign in!", "success")
        return redirect(url_for("signin"))

    return render_template("reset_with_token.html", form=form)

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.is_correct_password(form.currentpass.data):
            current_user.password = form.password.data
            db.session.commit()
            flash("Password changed!", "success")
            login_user(current_user, remember=True)
            return redirect(url_for("index"))
        else:
            flash("Current password incorrect, try again", "error")

    return render_template("change_password.html", form=form)

@app.route("/awards", methods=["GET", "POST"])
@login_required
def awards():
    p = phase()
    if p == 0:
        return render_template("nominees.html", awards=list_awards())
    if p == 2:
        return render_template("voting.html", form=VoteForm(),
            awards=list_awards())
    # else: nominations
    form = NominationForm()
    if form.validate_on_submit():
        award = Award.query.filter_by(id=form.award_id.data).first_or_404()
        if len(form.entry.data) < 1:
            flash("Cannot submit empty nominations", "error")
        elif len(form.entry.data) > 128:
            flash("Nominations must not exceed 128 characters", "error")
            form.entry.data = None
        else:
            award.nominations.append(Nomination(name=form.entry.data,
                                                creator=current_user))
            db.session.commit()
            flash("Nomination successful!", "success")
        return redirect(url_for("awards"))
    return render_template("nominations.html", form=form, awards=list_awards())

@app.route("/submit_vote", methods=["POST"])
@login_required
def submit_vote():
    result = { "success" : 0,
               "message" : "An error occurred" }
    if phase() != 2:
        result["message"] = "Not voting phase!"
        return json.dumps(result), 200 # return 200 so message displays

    form = VoteForm()
    if form.validate() or True:
        try:
            nom_id = int(form.nomid.data)
        except:
            return json.dumps(result), 200
        nom = Nomination.query.filter_by(id=nom_id).first()
        if nom is None:
            return json.dumps(result), 200
        for sel in current_user.selections:
            if sel in nom.award.nominations:
                # take away vote from other nom in this category
                # clicking same button will simply remove the vote
                current_user.selections.remove(sel)
                result["no_vote"] = str(sel.id)
                if sel == nom:
                    # we removed the vote, so we are done
                    result["success"] = 1
                    result["message"] = "Vote removed"
                    db.session.commit()
                    return json.dumps(result), 200
                break
        # only add vote if it was a different nomination's button
        nom.voters.append(current_user)
        result["success"] = 2
        result["message"] = "Vote submitted"
        result["vote"] = str(nom.id)
        db.session.commit()

    return json.dumps(result), 200

# Admin Interface

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        return current_user.is_admin

    def _handle_view(self, name, **kwds):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return login_manager.unauthorized()

    @expose("/", methods=["GET", "POST"])
    def index(self):
        spform = SetPhaseForm()
        pnform = PhaseNomForm()
        pvform = PhaseVoteForm()
        psform = PhaseStaticForm()
        bform = BanForm()
        aform = AdminForm()
        nform = NomIDForm()
        cform = ClearForm()

        if ((spform.static.data or spform.nom.data or spform.vote.data) and
                spform.validate_on_submit()):
            self.set_phase(spform)
            return self.check_full_index()
        if ((pnform.pnon.data and pnform.validate_on_submit()) or
                pnform.pnoff.data):
            self.phase_sched(pnform, 1)
            return self.check_full_index()
        if ((pvform.pvon.data and pvform.validate_on_submit()) or
                pvform.pvoff.data):
            self.phase_sched(pvform, 2)
            return self.check_full_index()
        if ((psform.pson.data and psform.validate_on_submit()) or
                psform.psoff.data):
            self.phase_sched(psform, 0)
            return self.check_full_index()
        if (bform.ban.data or bform.unban.data) and bform.validate_on_submit():
            if self.ban(bform):
                return self.check_full_index()
        if (aform.give.data or aform.take.data) and aform.validate_on_submit():
            self.change_admin(aform)
            return self.check_full_index()
        if ((nform.rem.data or nform.rwarn.data or nform.rban.data) and
                nform.validate_on_submit()):
            self.remove_nom(nform.nomid.data, nform.rwarn.data, nform.rban.data)
            return self.check_full_index()
        if ((cform.cnoms.data or cform.cvotes.data) and
                cform.validate_on_submit()):
            self.clear(cform)
            return self.check_full_index()

        full = self.get_full()
        s = State.query.first()
        if s.dtnom is not None:
            pnform.dtnom.data = s.dtnom
        if s.dtvote is not None:
            pvform.dtvote.data = s.dtvote
        if s.dtstatic is not None:
            psform.dtstatic.data = s.dtstatic

        return self.render("admin/index.html", spform=spform, pnform=pnform,
            pvform=pvform, psform=psform, aform=aform, bform=bform, nform=nform,
            cform=cform, awards=list_awards(), full=full, phase=phase())

    @expose("/noms/<awd>", methods=["GET", "POST"])
    def list_noms(self, awd):
        form = RemoveNomForm()
        if form.validate_on_submit():
            self.remove_nom(form.nomid.data, form.warn.data, form.ban.data)
            return redirect(url_for("admin.list_noms", awd=awd))
        award = Award.query.filter_by(id=awd).first_or_404()
        return self.render("admin/list_noms.html", form=form, award=award)

    @expose("/guide", methods=["GET"])
    def guide(self):
        return self.render("admin/guide.html")

    def set_phase(self, form):
        p = 0 if form.static.data else 1 if form.nom.data else 2
        assign_phase(p)
        flash("Phase changed to %s" %
            ("static", "nominating", "voting")[p], "success")

    def clear(self, form):
        if form.cnoms.data:
            clear_votes() # must be done first
            clear_noms()
            flash("Cleared all nominations", "success")
        elif form.cvotes.data:
            clear_votes()
            flash("Cleared all votes", "success")
        else:
            abort(400)

    def phase_sched(self, form, p):
        if p == 1:
            kwds = pndict
            cancel = form.pnoff.data
            dt = form.dtnom.data
            pname = "Nominating"
        elif p == 2:
            kwds = pvdict
            cancel = form.pvoff.data
            dt = form.dtvote.data
            pname = "Voting"
        else:
            kwds = psdict
            cancel = form.psoff.data
            dt = form.dtstatic.data
            pname = "Static"

        if cancel:
            try:
                scheduler.remove_job(kwds["id"])
                flash("Canceled %s Phase" % pname, "success")
            except JobLookupError:
                flash("%s Phase schedule not found or "
                      "already passed" % pname, "warning")
            dt = None
        else:
            scheduler.add_job(replace_existing=True,
                run_date=dt, **kwds)
            flash("Scheduled %s Phase for %s Eastern" %
                (pname, dt.strftime("%A %B %d %Y at %I:%M %p")), "success")

        s = State.query.first()
        if p == 1:
            s.dtnom = dt
        elif p == 2:
            s.dtvote = dt
        else:
            s.dtstatic = dt
        db.session.commit()

    def ban(self, bform):
        user = User.query.filter_by(
            username=bform.banuser.data.lower()).first_or_404()
        if bform.ban.data:
            user.ban()
            msg = "Banned "
            if bform.email.data:
                subject = "Your account has been banned"
                html = render_template("email/ban.html", award_name=None)
                msg += "and notified "
        elif bform.unban.data:
            user.unban()
            msg = "Unbanned "
            if bform.email.data:
                subject = "Your account is no longer banned"
                html = render_template("email/unban.html")
                msg += "and notified "
        db.session.flush()
        if not bform.email.data or send_email(user.email, subject, html):
            db.session.commit()
            flash(msg + user.username, "success") # flash once commit passes
            return True
        return False

    def change_admin(self, aform):
        user = User.query.filter_by(
            username=aform.adminuser.data.lower()).first_or_404()
        if aform.give.data:
            user.give_admin()
            msg = "Made %s an admin" % user.username
        elif aform.take.data:
            user.take_admin()
            msg = "Removed %s as admin" % user.username
        db.session.commit()
        flash(msg, "success") # flash once commit passes

    def remove_nom(self, nomid, warn, ban):
        nom = Nomination.query.filter_by(id=nomid).first_or_404()
        awd = nom.award
        user = nom.creator
        db.session.delete(nom) # any of the buttons will remove the nom
        msgs = ["Removed %r ('%s' for '%s')" % (nom, nom.name, awd.name)]
        if warn:
            subject = "Inappropriate Content Warning"
            html = render_template("email/warning.html", award_name=awd.name)
            msgs.append("Warning sent to %s" % user.username)
        elif ban:
            user.ban()
            subject = "Your account has been banned"
            html = render_template("email/ban.html", award_name=awd.name)
            msgs.append("Banned and notified %s" % user.username)
        db.session.flush()
        if not (warn or ban) or send_email(user.email, subject, html):
            db.session.commit()
            for msg in msgs: # flash once commit passes
                flash(msg, "success")
            return True
        return False

    def check_full_index(self):
        full = self.get_full()
        if full:
            return redirect("/admin/?full")
        else:
            return redirect("/admin/")

    def get_full(self):
        full = request.args.get("full")
        # if full appears as anything in request, render the full page
        return full is not None

class MyModelView(ModelView):
    form_base_class = SecureForm
    is_accessible = MyAdminIndexView.is_accessible
    _handle_view = MyAdminIndexView._handle_view
    column_display_pk = True

class UserView(MyModelView):
    column_exclude_list = ("_password", "sessTokenTime")

admin = Admin(app, name="Kudos Admin", template_mode="bootstrap3",
    index_view=MyAdminIndexView())
admin.add_view(UserView(User, db.session))
admin.add_view(MyModelView(Award, db.session))
admin.add_view(MyModelView(Nomination, db.session))
admin.add_view(MyModelView(State, db.session))

def handle_error(e):
    try:
        code = e.code
    except AttributeError:
        code = 500
    return render_template("error.html", error=e), code

def init_error_mail():
    class MySMTPHandler(SMTPHandler):
        def emit(self, record):
            if current_user and current_user.is_authenticated:
                record.username = current_user.username
            else:
                record.username = None
            return super().emit(record)

        def getSubject(self, record):
            return f"{self.subject} ({record.levelname}) - {record.asctime}"

    fromaddr = app.config["MAIL_USERNAME"]
    tls = app.config.get("MAIL_USE_TLS", False)
    ssl = app.config.get("MAIL_USE_SSL", False)
    secure = () if tls or ssl else None
    port = app.config["MAIL_PORT"] if not ssl else app.config["MAIL_PORT_TLS"]

    mail_handler = MySMTPHandler(
        mailhost=(app.config["MAIL_SERVER"], port),
        fromaddr=f"Kudos <{fromaddr}>",
        toaddrs=[fromaddr], # send it back to admin account
        subject="Kudos Failure",
        credentials=(fromaddr, app.config["MAIL_PASSWORD"]),
        secure=secure)
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s by User <%(username)s>:\n'
        '%(message)s'
    ))
    app.logger.addHandler(mail_handler)


for code in default_exceptions:
    app.register_error_handler(code, handle_error)

if not app.debug:
    init_error_mail()

def send_confirm_link(userID, email):
    subject = "Confirm your email"
    token = ts.dumps([userID, email], salt="email-confirm-key")
    confirm_url = url_for("confirm_email", token=token, _external=True)
    html = render_template("email/activate.html", confirm_url=confirm_url)
    return send_email(email, subject, html)

def try_send_msg(msg):
    st = StringIO()
    traceback.print_stack(limit=50, file=st)
    try:
        mail.send(msg)
    except Exception as e:
        msg = str(e) + "\n\nCalling stack:\n" + st.getvalue() + "\n"
        app.logger.exception(msg)
        flash("Email send error, try again", "error")
        db.session.rollback() # assume we always want to undo flush
        return False
    return True

def send_email(email, subject, html, **kwds):
    msg = Message("[KUDOS] " + subject, recipients=[email], html=html, **kwds)
    return try_send_msg(msg)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ("http", "https") and
            ref_url.netloc == test_url.netloc)

def phase():
    return State.query.first().phase

def list_awards():
    return Award.query.order_by(Award.order).all()

def assign_phase(p):
    s = State.query.first()
    s.phase = p
    db.session.commit()

pndict = dict(
    func=assign_phase,
    args=[1],
    id="nom",
    name="Change phase to nominating")
pvdict = dict(
    func=assign_phase,
    args=[2],
    id="vote",
    name="Change phase to voting")
psdict = dict(
    func=assign_phase,
    args=[0],
    id="static",
    name="Change phase to static")

@app.before_first_request
def initScheduler():
    # this implementation assumes there is only one dyno on heroku
    s = State.query.first()
    if s.dtnom is not None:
        scheduler.add_job(run_date=s.dtnom, **pndict)
    if s.dtvote is not None:
        scheduler.add_job(run_date=s.dtvote, **pvdict)
    if s.dtstatic is not None:
        scheduler.add_job(run_date=s.dtstatic, **psdict)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(debug=True) # should only be on debug when run locally
