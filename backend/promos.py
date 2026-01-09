from backend.models import Promo

def redeem_code(db, user, code):
    promo = db.query(Promo).filter(Promo.code == code, Promo.active == True).first()
    if not promo:
        return False

    user.credits += promo.credits
    promo.active = False
    db.commit()
    return True
