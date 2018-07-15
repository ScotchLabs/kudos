from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_sslify import SSLify
from itsdangerous import URLSafeTimedSerializer

#Set up SQL app
app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

mail = Mail(app)

SSLify(app) # force https, only when debug is false, breaks on localhost

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

award_order = ["Best Director",
"Best Production Manager",
"Best Stage Manager",
"Best Technical Director",
"Best Music Director",
"Best Choreography",
"Best Actress in a Lead Role",
"Best Actor in a Lead Role",
"Best Supporting Actress",
"Best Supporting Actor",
"Best Featured Performer",
"Best Ensemble",
"Best Duo",
"Best Improv Performer",
"Best Sketch Actor",
"Best Cover",
"Worst Cover",
"Best Set Design",
"Best Lighting",
"Best Sound",
"Best Costumes",
"Best Props",
"Best Publicity",
"Best Hair & Makeup",
"Best House",
"Best Original Work",
"Best Strike/Load-in Moment",
"Worst Strike/Load-in Moment",
"Best Prank",
"Most Likely to Injure Oneself",
"Kevin Perry Technical Insanity Award",
"Donkeypunch Award",
"Coolest Rookie",
"Coolest Veteran",
"Party Animal",
"Darren M. Canady Sassypants Award",
"Cutest Couple",
"Cutest Potential Couple",
"Most Successful Flirt",
"Least Successful Flirt",
"Most Corrupted",
"Shannon Deep S'n'S Mom Award",
'The "It Sounded Like A Good Idea at the Time" Award',
"King and Queen of the Black Chairs Award",
"Best Late Show Moment",
"Nathaniel Biggs Coolest Uncle Award",
"New Kudos Category",
"Retire a Kudos Category"]
