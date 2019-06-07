from app_manager import db
from models import User, Award, Nomination, State
import os, random

def init_db():
    db.drop_all()
    db.create_all()

    init_awards()
    init_state()

    db.session.commit()

def give_admin(username):
    user = User.query.filter_by(username="gseastre").first()
    if user is None:
        raise KeyError("User '%s' does not exist" % (username,))
    user.give_admin()

def init_state():
    db.session.query(State).delete()
    db.session.add(State(phase=0))
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
    "Best Improv Moment",
    "Best Sketch Actor",
    "Best Cover",
    "Worst Cover",
    "Best Set",
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
    "Nathan Blinn Best Black Chairs Argument",
    "New Kudos Category",
    "Retire a Kudos Category",
    ]

    for i in range(len(award_order)):
        db.session.add(Award(name=award_order[i], order=(i + 1) * 10))

    db.session.commit()

def init_some_noms():
    # Not destructive, will add these to the first 5 awards
    user = init_myself()
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
    awards[4].nominations.append(Nomination(name="That kid who played Igor", creator=user))

    db.session.commit()

def init_many_noms():
    user = init_myself()

    choices = [
    "Grant Seastream",
    "Stephen Colbert",
    "American Vandal",
    "Alex Trimboli",
    "Chicago",
    "Young Frankenstein",
    "That time everyone did that cool thing and it was amazing",
    "That time we didn't go to Kennywood",
    "Vermin Supreme",
    "Free ponies for all Americans",
    "No food in the stood thoot",
    "Simon says",
    "Listen to your mother",
    "Why can't weeeee be friends, why can't weeeeeeeeeeeee be friends???",
    "Never gonna give you up",
    "Never gonna let you down",
    "Can we like please rename the improv award I mean come on it's a team sport",
    "I hardly know her!",
    "Sweeney Todd",
    "Jimmy Fallon isn't funny",
    ]

    awards = db.session.query(Award).all()

    for awd in awards:
        for i in range(10):
            awd.nominations.append(Nomination(name=random.choice(choices), creator=user))

    db.session.commit()

def init_user_admin(username):
    tmp = User.query.filter_by(username=username).first()
    if tmp is not None:
        raise ValueError("User already exists")
    user = User(username=username, password="password",
        email_confirmed=True, is_admin=True)
    db.session.add(user)
    db.session.commit()
    return user

def init_myself():
    user = User.query.filter_by(username="gseastre").first()
    if user is None:
        user = init_user_admin("gseastre")
    return user

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
