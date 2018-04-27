from app_manager import db
from models import User, Award, Nomination, State

def init_db():
    db.drop_all()
    db.create_all()

    init_awards()
    init_state()

    db.session.commit()

def init_awards():
    db.session.query(Nomination).delete()
    db.session.query(Award).delete()

    awards = [
        Award(name="Best Director"),
        Award(name="Best Production Manager"),
        Award(name="Best Stage Manager"),
        Award(name="Best Technical Director"),
        Award(name="Best Music Director"),
        Award(name="Best Choreography"),
        Award(name="Best Actress in a Lead Role"),
        Award(name="Best Actor in a Lead Role"),
        Award(name="Best Supporting Actress"),
        Award(name="Best Supporting Actor"),
        Award(name="Best Featured Performer"),
        Award(name="Best Ensemble"),
        Award(name="Best Duo"),
        Award(name="Best Improv Performer"),
        Award(name="Best Sketch Actor"),
        Award(name="Best Cover"),
        Award(name="Worst Cover"),
        Award(name="Best Set Design"),
        Award(name="Best Lighting"),
        Award(name="Best Sound"),
        Award(name="Best Costumes"),
        Award(name="Best Props"),
        Award(name="Best Publicity"),
        Award(name="Best Hair & Makeup"),
        Award(name="Best Original Work"),
        Award(name="Best Strike/Load-in Moment"),
        Award(name="Worst Strike/Load-in Moment"),
        Award(name="Best Prank"),
        Award(name="Most Likely to Injure Oneself"),
        Award(name="Kevin Perry Technical Insanity Award"),
        Award(name="Donkeypunch Award"),
        Award(name="Coolest Rookie"),
        Award(name="Coolest Veteran"),
        Award(name="Party Animal"),
        Award(name="Darren M. Canady Sassypants Award"),
        Award(name="Cutest Couple"),
        Award(name="Cutest Potential Couple"),
        Award(name="Most Successful Flirt"),
        Award(name="Least Successful Flirt"),
        Award(name="Most Corrupted"),
        Award(name="Shannon Deep S'n'S Mom Award"),
        Award(name="The \"It Sounded Like A Good Idea at the Time\" Award"),
        Award(name="King and Queen of the Black Chairs Award"),
        Award(name="Best Late Show Moment"),
        Award(name="Nathanial Biggs Coolest Uncle Award"),
        Award(name="New Kudos Category"),
        Award(name="Retire a Kudos Category")
        ]

    for a in awards:
        db.session.add(a)

    db.session.commit()

def init_some_noms():
    """Not destructive, will add these to the first 5 awards"""
    user = User.query.filter_by(username="gseastre").first()
    if user is None:
        user = User(username="gseastre", password="iamgroont", email_confirmed=True)
        db.session.add(user)

    awards = db.session.query(Award).all()
    assert(len(awards) >= 5)

    awards[0].nominations.append(Nomination(name="Grant Seastream", creator=user))
    awards[0].nominations.append(Nomination(name="It's me", creator=user))
    awards[0].nominations.append(Nomination(name="Jared", creator=user))
    awards[1].nominations.append(Nomination(name="Grant Again", creator=user))
    awards[1].nominations.append(Nomination(name="It's me", creator=user))
    awards[2].nominations.append(Nomination(name="Stephen Colbert", creator=user))
    awards[3].nominations.append(Nomination(name="My butt", creator=user))
    awards[4].nominations.append(Nomination(name="Hey there!", creator=user))
    awards[4].nominations.append(Nomination(name="American Vandal", creator=user))
    awards[4].nominations.append(Nomination(name="Alex Trimboli", creator=user))
    awards[4].nominations.append(Nomination(name="Abby Pingboi", creator=user))

    db.session.commit()

def init_state():
    state = State(phase=0)
    db.session.add(state)
    db.session.commit()

def clear_votes():
    for user in User.query.all():
        if len(user.selections) > 0:
            user.selections = []
    db.session.commit()
