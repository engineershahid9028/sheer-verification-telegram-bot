from backend.models import User
from sqlalchemy.orm import Session

def get_or_create_user(user_id: int):
    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        user = User(id=user_id, credits=1.0)
        db.add(user)
        db.commit()
        db.refresh(user)

    # extract value BEFORE closing session
    credits = user.credits

    db.close()

    # return plain object instead of ORM object
    return {"id": user_id, "credits": credits}
