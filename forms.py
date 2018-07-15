from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app_manager import db
from models import User

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

def check_ban(form, field):
    exists(form, field)
    user = User.query.filter_by(username=field.data.lower()).first()
    if form.ban.data and user.banned:
        raise ValidationError("User is already banned")
    elif form.unban.data and not user.banned:
        raise ValidationError("User is not banned")

def check_admin(form, field):
    exists(form, field)
    user = User.query.filter_by(username=field.data.lower()).first()
    if form.give.data and user.is_admin:
        raise ValidationError("User is already admin")
    elif form.take.data and not user.is_admin:
        raise ValidationError("User is not admin")

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
