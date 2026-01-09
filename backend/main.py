print("🔥 BACKEND MAIN LOADED 🔥")
from fastapi import FastAPI
import traceback

app = FastAPI()

@app.get("/")
def root():
    try:
        return {"status": "ok"}
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/run")
def run(user_id: int, tool: str, args: str):
    return {"job_id": "123", "status": "queued"}
