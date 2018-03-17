from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app_manager import db
from models import User

passmin = 7
passmax = 128

def available(form, field):
    user = User.query.filter_by(username=field.data).first()
    if user is not None:
        raise ValidationError("Username already exists")

def exists(form, field):
    user = User.query.filter_by(username=field.data).first()
    if user is None:
        raise ValidationError("Username does not exist")

def is_banned(form, field):
    exists(form, field)
    user = User.query.filter_by(username=field.data).first()
    if not user.banned:
        raise ValidationError("User is not banned")

def is_not_banned(form, field):
    exists(form, field)
    user = User.query.filter_by(username=field.data).first()
    if user.banned:
        raise ValidationError("User is already banned")

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
    username = StringField('Andrew ID',
        validators=[DataRequired(), is_not_banned])

class UnbanForm(FlaskForm):
    username = StringField('Andrew ID',
        validators=[DataRequired(), is_banned])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])

class ChangePasswordForm(FlaskForm):
    currentpass = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])

class NominationForm(FlaskForm):
    entry = StringField('Nominate',
        validators=[DataRequired(), Length(max=128)])
