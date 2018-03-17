from flask import redirect, render_template, url_for, send_file, abort, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from urllib.parse import urlparse, urljoin
import itsdangerous
from app_manager import app, db, ts, mail, basic_auth
from forms import (SignupForm, LoginForm, UsernameForm, ResetPasswordForm,
                   ChangePasswordForm, NominationForm, BanForm, UnbanForm)
from models import User, Award, Nomination
import login_manager # just to run initialization

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()

        # Now we'll send the email confirmation link
        subject = "Confirm your email"

        token = ts.dumps(user.email, salt='email-confirm-key')

        confirm_url = url_for(
            'confirm_email',
            token=token,
            _external=True)

        html = render_template(
            'email/activate.html',
            confirm_url=confirm_url)

        send_email(user.email, subject, html)

        flash("Account created! Please click the confirmation link sent to "
              "your email")

        return redirect(url_for('index'))

    return render_template('signup.html', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except itsdangerous.SignatureExpired:
        return render_template("activate_expired.html", token=token)
    except:
        abort(404)

    user = User.query.filter_by(email=email).first_or_404()

    if user.email_confirmed == True:
        return "Your email has already been confirmed, silly!"

    user.email_confirmed = True

    db.session.add(user)
    db.session.commit()

    flash("Email confirmed! Sign in!")

    return redirect(url_for('signin'))

@app.route("/newlink/<token>")
def new_link(token):
    email = ts.loads(token, salt="email-confirm-key") # no max_age

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

    flash("New confirmation link sent, check your email!")

    return redirect(url_for('index'))

@app.route('/signin', methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first_or_404()
        if not user.email_confirmed:
            flash("Please click the confirmation link sent to your email first")
            return redirect(url_for("signin"))
        if user.is_correct_password(form.password.data):
            if user.banned:
                flash("Your account has been banned")
                return redirect(url_for("signin"))
            login_user(user, remember=True)
            flash('Logged in successfully')
            next_url = request.args.get('next')
            if not is_safe_url(next_url):
                return abort(400)
            return redirect(next_url or url_for('index'))
        else:
            flash('Password incorrect, try again')
            return redirect(url_for('signin'))
    return render_template('signin.html', form=form)

@app.route('/signout')
@login_required
def signout():
    logout_user()
    flash("Logged out")
    return redirect(url_for('index'))

@app.route('/reset', methods=["GET", "POST"])
def reset():
    form = UsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first_or_404()

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

        flash("Password reset link sent to your email address")

        return redirect(url_for('index'))
    return render_template('reset.html', form=form)

@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        email = ts.loads(token, salt="recover-key", max_age=1800)
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

        flash("Password reset successfully!")

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
            flash("Password changed!")
            return redirect(url_for('index'))
        else:
            flash("Current password incorrect, try again")

    return render_template('change_password.html', form=form)

@app.route("/awards", methods=["GET", "POST"])
@login_required
def awards():
    form = NominationForm()
    if form.validate_on_submit():
        award = Award.query.filter_by(id=int(request.args.get('award'))).first_or_404()
        award.nominations.append(Nomination(name=form.entry.data, creator=current_user))
        db.session.add(award)
        db.session.commit()
        flash("Nomination successful!")
        return redirect(url_for("awards"))
    return render_template('awards.html', form=form, awards=Award.query.all())

@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    bform = BanForm()
    uform = UnbanForm()
    return render_template("admin.html", bform=bform, uform=uform,
                           awards=Award.query.all())

@app.route("/admin/ban", methods=["POST"])
@basic_auth.required
def ban():
    bform = BanForm()
    if bform.validate_on_submit():
        user = User.query.filter_by(username=bform.username.data).first_or_404()
        user.ban()
        db.session.add(user)
        db.session.commit()
        flash("Banned %s" % user.username)
        return redirect(url_for("admin"))
    uform = UnbanForm()
    return render_template("admin.html", bform=bform, uform=uform,
                           awards=Award.query.all())

@app.route("/admin/unban", methods=["POST"])
@basic_auth.required
def unban():
    uform = UnbanForm()
    if uform.validate_on_submit():
        user = User.query.filter_by(username=uform.username.data).first_or_404()
        user.unban()
        db.session.add(user)
        db.session.commit()
        flash("Unbanned %s" % user.username)
        return redirect(url_for("admin"))
    bform = BanForm()
    return render_template("admin.html", bform=bform, uform=uform,
                           awards=Award.query.all())

@app.route("/admin/remove", methods=["GET"])
@basic_auth.required
def remove():
    n = request.args.get('nom')
    u = request.args.get('user')
    if n is not None:
        nom = Nomination.query.filter_by(id=int(n)).first_or_404()
        db.session.delete(nom)
        db.session.commit()
    if u is not None:
        user = User.query.filter_by(id=int(u)).first_or_404()
        user.ban()
        db.session.add(user)
        db.session.commit()
        flash("Banned %s" % user.username)
    return redirect(url_for("admin"))

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

def send_email(email, subject, html):
    msg = Message(subject, recipients=[email], html=html)
    mail.send(msg)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)

if __name__ == "__main__":
    app.run()
