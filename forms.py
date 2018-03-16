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

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])

class ChangePasswordForm(FlaskForm):
    currentpass = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password',
        validators=[DataRequired(), Length(min=passmin, max=passmax)])
