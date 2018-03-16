from flask import redirect, render_template, url_for, send_file, abort, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from urllib.parse import urlparse, urljoin
import itsdangerous
from app_manager import app, db, ts, mail
from forms import (SignupForm, LoginForm, UsernameForm, ResetPasswordForm,
                   ChangePasswordForm)
from models import User
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

        return redirect(url_for('index'))

    return render_template('signup.html', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except itsdangerous.SignatureExpired:
        return "Uh oh! Your link expired! Please register again maybe"
    except:
        abort(404)

    user = User.query.filter_by(email=email).first_or_404()

    if user.email_confirmed == True:
        return "Your email has already been confirmed, silly!"

    user.email_confirmed = True

    db.session.add(user)
    db.session.commit()

    return redirect(url_for('signin'))

@app.route('/signin', methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first_or_404()
        if user.is_correct_password(form.password.data):
            login_user(user, remember=True)
            flash('Logged in successfully')
            next_url = session.pop('next', None)
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

        return redirect(url_for('index'))
    return render_template('reset.html', form=form)

@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        email = ts.loads(token, salt="recover-key", max_age=86400)
    except itsdangerous.SignatureExpired:
        return "Uh oh! Your link expired! Please click again maybe"
    except:
        abort(404)

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()

        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('signin'))

    return render_template('reset_with_token.html', form=form, token=token)

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first_or_404()

        if user.is_correct_password(form.currentpass.data):
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            flash("Current password incorrect, try again")

    return render_template('change_password.html', form=form)

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
