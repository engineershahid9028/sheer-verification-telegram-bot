from datetime import datetime, timedelta

def claim_daily(user, db):
    if user.last_daily and datetime.utcnow() - user.last_daily < timedelta(days=1):
        return False

    user.credits += 1
    user.last_daily = datetime.utcnow()
    db.commit()
    return True
