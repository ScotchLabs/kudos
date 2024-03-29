from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_sslify import SSLify
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer

#Set up SQL app
app = Flask(__name__)
app.config.from_object("config")

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

mail = Mail(app)

SSLify(app) # force https, only when debug is false, breaks on localhost

migrate = Migrate(app, db, compare_type=True)

DAY = 86400

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

serializer = URLSafeSerializer(app.config["SECRET_KEY"]) # for session tokens
