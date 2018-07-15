from app_manager import db
from models import User, Award, Nomination, State
import os

def init_db():
    db.drop_all()
    db.create_all()

    init_awards()
    init_state()

    db.session.commit()

def init_awards():
    db.session.query(Nomination).delete()
    db.session.query(Award).delete()

    award_order = [
    "Best Director",
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
    "Retire a Kudos Category",
    ]

    awards = []
    for i in range(len(award_order)):
        awards.append(Award(name=award_order[i], order=(i + 1) * 10))

    for a in awards:
        db.session.add(a)

    db.session.commit()

def init_some_noms():
    """Not destructive, will add these to the first 5 awards"""
    user = User.query.filter_by(username="gseastre").first()
    if user is None:
        user = User(username="gseastre", password="iamgroont",
            email_confirmed=True, is_admin=True)
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

def delete_award(award):
    # delete all children nominations first
    for nom in award.nominations:
        db.session.delete(nom)
    db.session.delete(award)
    db.session.commit()

def remove_local_db():
    os.remove("data.db")
