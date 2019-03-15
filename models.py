from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
import time
from app_manager import db, bcrypt

users = db.Table('users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('nom_id', db.Integer, db.ForeignKey('nomination.id'),
              primary_key=True)
)

def default_email(context):
    # Andrew email should be used, but it could be different
    if context is None:
        # flask_admin's create interface will pass None for context
        return "email@domain.com"
    return context.get_current_parameters()["username"] + "@andrew.cmu.edu"

def default_password():
    return bcrypt.generate_password_hash("password")

def default_token():
    return bcrypt.generate_password_hash(str(time.time()))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    _password = db.Column(db.String(128), nullable=False,
                          default=default_password)
    email = db.Column(db.String(128), nullable=False, default=default_email)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    session_token = db.Column(db.String(128), nullable=False,
                              default=default_token)
    banned = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = \
            bcrypt.generate_password_hash(plaintext).decode('utf-8')
        self.reset_token() # reset the token when you change the password

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)

    def reset_token(self):
        self.session_token = bcrypt.generate_password_hash(str(time.time()))

    def ban(self):
        self.banned = True
        self.reset_token() # invalidate their sessions

    def unban(self):
        self.banned = False

    def give_admin(self):
        self.is_admin = True

    def take_admin(self):
        self.is_admin = False

    # Flask-Login properties
    @property
    def is_authenticated(self):
        return self.email_confirmed

    @property
    def is_active(self):
        return not self.banned

    def get_id(self):
        return self.session_token

    def __repr__(self):
        return '<User %r>' % self.username

class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    nominations = db.relationship("Nomination", backref="award")
    order = db.Column(db.Integer, nullable=False, default=1000)

    def __repr__(self):
        return '<Award %r>' % self.name

class Nomination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    award_id = db.Column(db.Integer, db.ForeignKey('award.id'), nullable=False)
    creator = db.relationship("User", backref="entries")
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voters = db.relationship("User", secondary=users,
                             backref=db.backref("selections"))

    @property
    def votes(self):
        return len(self.voters)

    def __repr__(self):
        return '<Nomination %r>' % self.id

class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 0 is static, 1 is nominations, 2 is voting
    phase = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<State %r>' % self.id
