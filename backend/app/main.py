from fastapi import FastAPI

app = FastAPI(title="SkillFit API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}
