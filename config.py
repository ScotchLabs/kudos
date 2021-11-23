import os

try:
    from config_secrets import key, email, password
except ImportError:
    key = email = password = None

DEBUG = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
uri = os.getenv("DATABASE_URL", "sqlite:///data.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
SQLALCHEMY_DATABASE_URI = uri
SECRET_KEY = os.getenv("SECRET_KEY", key)
BCRYPT_LOG_ROUNDS = 12
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_PORT_TLS = 587 # for SMTPHandler
MAIL_USE_SSL = True
MAIL_USERNAME = os.getenv("MAIL_USERNAME", email)
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", password)
MAIL_DEFAULT_SENDER = ("Kudos", MAIL_USERNAME)
REMEMBER_COOKIE_DURATION = 5184000 # 60 days
