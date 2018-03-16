from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from app_manager import db, bcrypt

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(16), unique=True)
    _password = db.Column(db.String(128))
    email_confirmed = db.Column(db.Boolean, default=False)

    @hybrid_property
    def email(self):
        return self.username + "@andrew.cmu.edu"

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)

    @property
    def is_authenticated(self):
        # redefine this over UserMixin
        return self.email_confirmed

    def __repr__(self):
        return '<User %r %r>' % (self.id, self.username)

class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Awards %r>' % self.id
