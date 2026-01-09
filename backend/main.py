from fastapi import FastAPI

print("🔥 BACKEND MAIN LOADED 🔥")

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
