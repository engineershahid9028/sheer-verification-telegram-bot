def apply_referral(new_user, referrer_id, db):
    referrer = db.query(User).filter(User.id == referrer_id).first()
    if not referrer:
        return False

    new_user.referred_by = referrer_id
    new_user.credits += 1
    referrer.credits += 1
    db.commit()
    return True
