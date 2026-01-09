def activate_subscription(user, db):
    user.subscription = True
    user.credits += 20
    db.commit()
