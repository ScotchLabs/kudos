from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app_manager import db
from models import User, Nomination

passmin = 7
passmax = 128

def available(form, field):
    user = User.query.filter_by(username=field.data.lower()).first()
    if user is not None:
        raise ValidationError("Username already exists")

def exists(form, field):
    user = User.query.filter_by(username=field.data.lower()).first()
    if user is None:
        raise ValidationError("Username does not exist")
    return user

def check_ban(form, field):
    user = exists(form, field)
    if form.ban.data and user.banned:
        raise ValidationError("User is already banned")
    elif form.unban.data and not user.banned:
        raise ValidationError("User is not banned")

def check_admin(form, field):
    user = exists(form, field)
    if form.give.data and user.is_admin:
        raise ValidationError("User is already admin")
    elif form.take.data and not user.is_admin:
        raise ValidationError("User is not admin")

def check_nom(form, field):
    nomid = integer(form, field)
    nom = Nomination.query.filter_by(id=nomid).first()
    if nom is None:
        raise ValidationError("Nomination ID does not exist")

def integer(form, field):
    try:
        i = int(field.data)
    except ValueError:
        raise ValidationError("Must be an integer") from None
    return i

class SignupForm(FlaskForm):
    username = StringField('Andrew ID',
        validators=[DataRequired(), Length(max=16), available])
    password = PasswordField('Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])

class LoginForm(FlaskForm):
    username = StringField('Andrew ID', validators=[DataRequired(), exists])
    password = PasswordField('Password', validators=[DataRequired()])

class UsernameForm(FlaskForm):
    username = StringField('Andrew ID', validators=[DataRequired(), exists])

class BanForm(FlaskForm):
    banuser = StringField('Username', validators=[DataRequired(), check_ban])
    ban = SubmitField('Ban User')
    unban = SubmitField('Unban User')

class AdminForm(FlaskForm):
    adminuser = StringField('Username',
        validators=[DataRequired(), check_admin])
    give = SubmitField('Give Admin')
    take = SubmitField('Take Admin')

class NomIDForm(FlaskForm):
    nomid = StringField('Nomination ID', validators=[DataRequired(), check_nom])
    rem = SubmitField('Remove')
    rwarn = SubmitField('Remove & Warn')
    rban = SubmitField('Remove, Ban, & Notify')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])

class ChangePasswordForm(FlaskForm):
    currentpass = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])

class NominationForm(FlaskForm):
    entry = StringField('Nomination')
    award_id = HiddenField('Award ID')
