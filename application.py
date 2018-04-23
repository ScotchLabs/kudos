from flask import redirect, render_template, url_for, send_file, abort, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from urllib.parse import urlparse, urljoin
import itsdangerous
import json
from app_manager import app, db, ts, mail, basic_auth
from forms import (SignupForm, LoginForm, UsernameForm, ResetPasswordForm,
                   ChangePasswordForm, NominationForm, BanForm, UnbanForm)
from models import User, Award, Nomination, State
import login_manager # just to run initialization

application = app # name needed for eb

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.lower(), password=form.password.data)
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
        user = User.query.filter_by(username=form.username.data.lower()).first_or_404()
        if user.email_confirmed == True:
            flash("Your email is already confirmed!", "error")
            return render_template('resend.html', form=form)
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
        user = User.query.filter_by(username=form.username.data.lower()).first_or_404()
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
        user = User.query.filter_by(username=form.username.data.lower()).first_or_404()

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
    if phase() == 0:
        return render_template("nominees.html", awards=Award.query.all())
    if phase() == 2:
        return render_template("voting.html", awards=Award.query.all())
    # else: nominations
    form = NominationForm()
    if form.validate_on_submit():
        if len(form.entry.data) < 1:
            flash("Cannot submit empty nominations", "error")
        elif len(form.entry.data) > 128:
            flash("Nominations must not exceed 128 characters", "error")
            form.entry.data = None
        else:
            award = Award.query.filter_by(id=int(request.args.get('award'))).first_or_404()
            award.nominations.append(Nomination(name=form.entry.data, creator=current_user))
            db.session.add(award)
            db.session.commit()
            flash("Nomination successful!", "success")
            return redirect(url_for("awards"))
    return render_template('nominations.html', form=form, awards=Award.query.all())

@app.route("/submit_vote", methods=["POST"])
@login_required
def submit_vote():
    result = { "success" : 0,
               "message" : "An error occurred" }
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

@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    bform = BanForm()
    uform = UnbanForm()
    return render_template("admin.html", bform=bform, uform=uform,
                           awards=Award.query.all(), phase=phase())

@app.route("/admin/ban", methods=["POST"])
@basic_auth.required
def ban():
    bform = BanForm()
    if bform.validate_on_submit():
        user = User.query.filter_by(username=bform.username.data.lower()).first_or_404()
        user.ban()
        db.session.add(user)
        db.session.commit()
        flash("Banned %s" % user.username, "success")
        return redirect(url_for("admin"))
    uform = UnbanForm()
    return render_template("admin.html", bform=bform, uform=uform,
                           awards=Award.query.all(), phase=phase())

@app.route("/admin/unban", methods=["POST"])
@basic_auth.required
def unban():
    uform = UnbanForm()
    if uform.validate_on_submit():
        user = User.query.filter_by(username=uform.username.data.lower()).first_or_404()
        user.unban()
        db.session.add(user)
        db.session.commit()
        flash("Unbanned %s" % user.username, "success")
        return redirect(url_for("admin"))
    bform = BanForm()
    return render_template("admin.html", bform=bform, uform=uform,
                           awards=Award.query.all(), phase=phase())

@app.route("/admin/remove", methods=["GET"])
@basic_auth.required
def remove():
    n = request.args.get('nom', type=int)
    w = request.args.get('warn', type=int)
    b = request.args.get('ban', type=int)
    if n is not None:
        nom = Nomination.query.filter_by(id=n).first_or_404()
        db.session.delete(nom)
        db.session.commit()
    if w is not None:
        user = User.query.filter_by(id=w).first_or_404()
        subject = "Inappropriate Content Warning"
        html = render_template('email/warning.html')
        send_email(user.email, subject, html)
        flash("Warning sent to %s" % user.username, "success")
    if b is not None:
        user = User.query.filter_by(id=b).first_or_404()
        user.ban()
        db.session.add(user)
        db.session.commit()
        flash("Banned %s" % user.username, "success")
    return redirect(url_for("admin"))

@app.route("/admin/setphase", methods=["GET"])
@basic_auth.required
def set_phase():
    p = request.args.get('phase', type=int)
    if p is not None:
        if not p in (0,1,2):
            abort(404)
        db.session.query(State).first().phase = p
        db.session.commit()
        flash("Phase changed to %s" % ("static", "nominating", "voting")[p], "success")
    return redirect(url_for("admin"))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", phase=phase())

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

if __name__ == "__main__":
    app.run(debug=True) # should only be on debug when run locally, not on eb
