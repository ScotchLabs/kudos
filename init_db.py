from app_manager import db
from models import User, Award, Nomination

def init_db():
    db.create_all()

    db.session.query(User).delete()
    db.session.query(Award).delete()
    db.session.query(Nomination).delete()

    u1 = User(username="gseastre", password="iamgroont", email_confirmed=True)
    awards = [Award(name="Best Actor"),
              Award(name="Worst Actor"),
              Award(name="Best Late Show Moment"),
              Award(name="The Alex Diclaudio 'Spackle' Award"),
              Award(name="Best Prop")]

    for a in awards:
        db.session.add(a)

    awards[0].nominations.append(Nomination(name="Grant Seastream", creator=u1))
    awards[0].nominations.append(Nomination(name="It's me", creator=u1))
    awards[0].nominations.append(Nomination(name="Jared", creator=u1))
    awards[1].nominations.append(Nomination(name="Grant Again", creator=u1))
    awards[1].nominations.append(Nomination(name="It's me", creator=u1))
    awards[3].nominations.append(Nomination(name="My butt", creator=u1))
    awards[4].nominations.append(Nomination(name="Hey there!", creator=u1))
    awards[4].nominations.append(Nomination(name="American Vandal", creator=u1))
    awards[4].nominations.append(Nomination(name="Alex Trimboli", creator=u1))
    awards[4].nominations.append(Nomination(name="Abby Pingboi", creator=u1))

    db.session.commit()


if __name__ == '__main__':
    init_db()
