import os

try:
    from secrets import key, email, password
except ImportError:
    key = email = password = None

DEBUG = False
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db")
SECRET_KEY = os.getenv("SECRET_KEY", key)
BCRYPT_LOG_ROUNDS = 12
SQLALCHEMY_TRACK_MODIFICATIONS = False
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = os.getenv("SECRET_KEY", email)
MAIL_PASSWORD = os.getenv("SECRET_KEY", password)
MAIL_DEFAULT_SENDER = MAIL_USERNAME
REMEMBER_COOKIE_DURATION = 1209600 # 2 weeks