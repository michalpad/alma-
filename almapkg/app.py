"""
ALMA — נקודת כניסה לשרת (FastAPI).
גרסת עלייה נקייה: מוודאת שהשרת עולה ועונה. הלוגיקה המלאה
(הקנייה/תרגול/קול) מתחברת בהדרגה דרך המודולים שב-almapkg/ai.
"""
from __future__ import annotations
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ALMA", description="מורה AI למתמטיקה ליסודי", version="1.0")


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "ALMA",
        "message": "אלמה פעילה!",
        "gemini_key_configured": bool(os.environ.get("GEMINI_API_KEY")),
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


class EchoIn(BaseModel):
    text: str


@app.post("/echo")
def echo(body: EchoIn):
    return {"received": body.text, "ok": True}


@app.get("/modules")
def modules():
    available = {}
    for name in ["practice_engine", "orchestrator", "prompts", "cost_optimizer",
                 "subscription", "cognitive_levels", "placement"]:
        try:
            __import__(f"almapkg.ai.{name}")
            available[name] = True
        except Exception as e:
            available[name] = f"error: {type(e).__name__}"
    return {"modules": available}
