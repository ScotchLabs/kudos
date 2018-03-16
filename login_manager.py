from flask_login import LoginManager
from app_manager import app
from models import User

login_manager = LoginManager(app)
login_manager.login_view =  "signin"

@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()
