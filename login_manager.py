from flask_login import LoginManager
from app_manager import app, serializer
from models import User

login_manager = LoginManager(app)
login_manager.login_view =  "signin"
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(session_token):
    try:
        uid, tokTime = serializer.loads(session_token, salt="session")
        u = User.query.filter_by(id=uid, sessTokenTime=tokTime).first()
        if u is not None and u.is_active:
            # refuse to recognize inactive accounts
            # this won't reset their token, but they won't appear logged in
            return u
    except:
        pass
    return None
