from backend.database import SessionLocal, init_db
from backend.models import Tool

init_db()
db = SessionLocal()

tools = [
    "youtube-verify-tool",
    "spotify-verify-tool",
    "k12-verify-tool",
    "one-verify-tool",
    "perplexity-verify-tool",
    "canva-teacher-tool",
    "veterans-verify-tool",
    "boltnew-verify-tool",
]

for name in tools:
    if not db.query(Tool).filter(Tool.name == name).first():
        db.add(Tool(name=name, price=1))

db.commit()
db.close()
print("✅ Tools seeded")
