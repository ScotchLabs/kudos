import itsdangerous, json, atexit

from flask import redirect, render_template, url_for, send_file, abort, \
    flash, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

from app_manager import app, db, ts, mail
from forms import SignupForm, LoginForm, UsernameForm, ResetPasswordForm, \
    ChangePasswordForm, NominationForm, BanForm, AdminForm, NomIDForm
from models import User, Award, Nomination, State
from login_manager import login_manager

from werkzeug.exceptions import default_exceptions
from urllib.parse import urlparse, urljoin
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.parser import parse
from dateutil.tz import gettz

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.lower(),
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()

        # Now we'll send the email confirmation link
        send_confirm_link(user.email)

        flash("Account created! Please click the confirmation link sent to "
              "your email", "success")

        return redirect(url_for('index'))

    return render_template('signup.html', form=form)

@app.route('/confirm/<token>', methods=["GET"])
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except itsdangerous.SignatureExpired:
        return render_template("activate_expired.html", token=token)
    except:
        abort(404)

    user = User.query.filter_by(email=email).first_or_404()

    if user.email_confirmed == True:
        return render_template("already_confirmed.html", token=token)

    user.email_confirmed = True

    db.session.add(user)
    db.session.commit()

    flash("Email confirmed! Sign in!", "success")

    return redirect(url_for('signin'))

@app.route("/newlink/<token>", methods=["GET"])
def new_link(token):
    email = ts.loads(token, salt="email-confirm-key") # ignore age here
    send_confirm_link(email)
    flash("New confirmation link sent, check your email!", "success")
    return redirect(url_for('index'))

@app.route('/resend', methods=["GET", "POST"])
def resend():
    form = UsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data.lower()).first_or_404()
        if user.email_confirmed == True:
            flash("Your email is already confirmed!", "error")
        else:
            send_confirm_link(user.email)
            flash("New confirmation link sent, check your email!", "success")
            return redirect(url_for('index'))
    return render_template('resend.html', form=form)

@app.route('/signin', methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
            next_url = request.args.get('next')
            if not is_safe_url(next_url):
                return abort(400)
            return redirect(next_url or url_for('index'))
        else:
            flash("Password incorrect, try again", "error")
            return redirect(url_for('signin'))
    return render_template('signin.html', form=form)

@app.route('/signout', methods=["GET"])
@login_required
def signout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for('index'))

@app.route('/reset', methods=["GET", "POST"])
def reset():
    form = UsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data.lower()).first_or_404()

        subject = "Password reset requested"

        token = ts.dumps(user.email, salt='recover-key')

        recover_url = url_for(
            'reset_with_token',
            token=token,
            _external=True)

        html = render_template(
            'email/recover.html',
            recover_url=recover_url)

        send_email(user.email, subject, html)

        flash("A password reset link has sent to your email address", "success")

        return redirect(url_for('index'))
    return render_template('reset.html', form=form)

@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        email = ts.loads(token, salt="recover-key", max_age=86400)
    except itsdangerous.SignatureExpired:
        return render_template("recover_expired.html")
    except:
        abort(404)

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()

        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        flash("Password reset successfully! Sign in!", "success")

        return redirect(url_for('signin'))

    return render_template('reset_with_token.html', form=form, token=token)

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.is_correct_password(form.currentpass.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            login_user(current_user, remember=True)
            flash("Password changed!", "success")
            return redirect(url_for('index'))
        else:
            flash("Current password incorrect, try again", "error")

    return render_template('change_password.html', form=form)

@app.route("/awards", methods=["GET", "POST"])
@login_required
def awards():
    p = phase()
    if p == 0:
        return render_template("nominees.html", awards=list_awards())
    if p == 2:
        return render_template("voting.html", awards=list_awards())
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
            db.session.add(award)
            db.session.commit()
            flash("Nomination successful!", "success")
        return redirect(url_for("awards") + "#" + str(award.id))
    return render_template('nominations.html', form=form, awards=list_awards())

@app.route("/submit_vote", methods=["POST"])
@login_required
def submit_vote():
    result = { "success" : 0,
               "message" : "An error occurred" }
    if phase() != 2:
        result["message"] = "Not voting phase!"
        return json.dumps(result), 200
    nom_id = request.form["nom"]
    try:
        if nom_id is None:
            raise ValueError
        nom_id = int(nom_id)
    except ValueError:
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

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", phase=phase())

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
        bform = BanForm()
        aform = AdminForm()
        nform = NomIDForm()
        if (bform.ban.data or bform.unban.data) and bform.validate_on_submit():
            self.ban(bform)
            return self.check_full_index()
        if (aform.give.data or aform.take.data) and aform.validate_on_submit():
            self.change_admin(aform)
            return self.check_full_index()
        if ((nform.rem.data or nform.rwarn.data or nform.rban.data) and
                nform.validate_on_submit()):
            self.remove_nom(nform.nomid.data, nform.rwarn.data, nform.rban.data)
            return self.check_full_index()
        full = self.get_full()
        return self.render("admin/index.html", bform=bform, aform=aform,
            nform=nform, awards=list_awards(), full=full, phase=phase())

    @expose("/user_list", methods=["GET"])
    def list_users(self):
        return self.render("admin/list_users.html", users=User.query.all())

    @expose("/noms", methods=["GET"])
    def list_noms(self):
        a = request.args.get('awd', type=int)
        award = Award.query.filter_by(id=a).first_or_404()
        return self.render("admin/list_noms.html", award=award)

    @expose("/remove", methods=["GET"])
    def remove(self):
        # url used by the nom list subpages to remove and such
        # it doesn't matter what actual argument is passed for warn or ban
        a = request.args.get('awd', type=int)
        n = request.args.get('nom', type=int)
        w = request.args.get('warn')
        b = request.args.get('ban')
        if n is not None:
            self.remove_nom(n, w is not None, b is not None)
        return redirect(url_for("admin.list_noms", awd=a))

    @expose("/setphase", methods=["GET"])
    def set_phase(self):
        p = request.args.get('phase', type=int)
        if p is not None:
            if not p in (0,1,2):
                abort(404)
            assign_phase(p)
            flash("Phase changed to %s" % ("static", "nominating", "voting")[p],
                  "success")
        return self.check_full_index()

    def ban(self, bform):
        user = User.query.filter_by(
            username=bform.banuser.data.lower()).first_or_404()
        msg = None
        if bform.ban.data:
            user.ban()
            msg = ("Banned %s" % user.username, "success")
        elif bform.unban.data:
            user.unban()
            msg = ("Unbanned %s" % user.username, "success")
        db.session.add(user)
        db.session.commit()
        if msg is not None:
            flash(*msg) # don't flash until commit passes

    def change_admin(self, aform):
        user = User.query.filter_by(
            username=aform.adminuser.data.lower()).first_or_404()
        msg = None
        if aform.give.data:
            user.give_admin()
            msg = ("Made %s an admin" % user.username, "success")
        elif aform.take.data:
            user.take_admin()
            msg = ("Removed %s as admin" % user.username, "success")
        db.session.add(user)
        db.session.commit()
        if msg is not None:
            flash(*msg) # don't flash until commit passes

    def remove_nom(self, nomid, warn, ban):
        nom = Nomination.query.filter_by(id=nomid).first_or_404()
        awd = nom.award
        user = nom.creator
        # any of the buttons will remove the nom
        db.session.delete(nom)
        db.session.commit()
        flash("Removed %r ('%s' for '%s')" % (nom, nom.name, awd.name),
              "success")
        if warn:
            subject = "Inappropriate Content Warning"
            html = render_template('email/warning.html', award_name=awd.name)
            send_email(user.email, subject, html)
            flash("Warning sent to %s" % user.username, "success")
        elif ban:
            user.ban()
            db.session.add(user)
            db.session.commit() # don't send email until commit passes
            subject = "Your account has been banned"
            html = render_template('email/ban.html')
            send_email(user.email, subject, html)
            flash("Banned and notified %s" % user.username, "success")

    def check_full_index(self):
        full = self.get_full()
        if full:
            return redirect("/admin/?full")
        else:
            return redirect("/admin/")

    def get_full(self):
        full = request.args.get('full')
        # if full appears as anything in request, render the full page
        return full is not None

class MyModelView(ModelView):
    is_accessible = MyAdminIndexView.is_accessible
    _handle_view = MyAdminIndexView._handle_view

class UserView(MyModelView):
    column_exclude_list = ['_password', "session_token"]

admin = Admin(app, name='Kudos Admin', template_mode='bootstrap3',
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

for code in default_exceptions:
    app.register_error_handler(code, handle_error)

def send_confirm_link(email):
    subject = "Confirm your email"

    token = ts.dumps(email, salt='email-confirm-key')

    confirm_url = url_for(
        'confirm_email',
        token=token,
        _external=True)

    html = render_template(
        'email/activate.html',
        confirm_url=confirm_url)

    send_email(email, subject, html)

def send_email(email, subject, html):
    msg = Message("[KUDOS] " + subject, recipients=[email], html=html)
    mail.send(msg)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)

def phase():
    return State.query.first().phase

def list_awards():
    return Award.query.order_by(Award.order).all()

def assign_phase(p):
    obj = State.query.first()
    obj.phase = p
    db.session.add(obj)
    db.session.commit()

@app.before_first_request
def initScheduler():
    tzinfos = {"EDT": gettz("US/Eastern")}
    nom = dict(
        func=assign_phase,
        args=[1],
        run_date=parse("2019-04-29 10:00:00 AM EDT", tzinfos=tzinfos),
        id='nom',
        name='Change phase to nominating')
    vote = dict(
        func=assign_phase,
        args=[2],
        run_date=parse("2019-05-02 11:59:00 PM EDT", tzinfos=tzinfos),
        id='vote',
        name='Change phase to voting')
    static = dict(
        func=assign_phase,
        args=[0],
        run_date=parse("2019-05-04 11:59:00 PM EDT", tzinfos=tzinfos),
        id='static',
        name='Change phase to static')

    scheduler = BackgroundScheduler()
    scheduler.add_job(**nom)
    scheduler.add_job(**vote)
    scheduler.add_job(**static)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(debug=True) # should only be on debug when run locally
