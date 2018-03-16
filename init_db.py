from app_manager import db
from models import User

def init_db():
    db.create_all()

    db.session.query(User).delete()

    db.session.commit()


if __name__ == '__main__':
    init_db()
