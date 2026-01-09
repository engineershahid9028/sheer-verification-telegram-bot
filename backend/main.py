from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/run")
def run(user_id: int, tool: str, args: str):
    return {"ok": True}
