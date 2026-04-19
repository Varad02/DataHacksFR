"""OpenAI-powered neighborhood risk explainer (FastAPI endpoint)."""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY) if API_KEY else None


class TractInfo(BaseModel):
    tract: str
    name: str = ""
    mean_loss_per_household: float
    median_home_value: float
    median_income: float
    damage_ratio: float = 0.0


@app.post("/api/explain")
async def explain(info: TractInfo) -> dict:
    if client is None:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not set")

    prompt = (
        f"You are an earthquake risk analyst. Explain in 2-3 plain-English sentences "
        f"the seismic risk for this neighborhood:\n"
        f"- Name: {info.name or info.tract}\n"
        f"- Expected loss per household: ${info.mean_loss_per_household:,.0f}\n"
        f"- Median home value: ${info.median_home_value:,.0f}\n"
        f"- Median household income: ${info.median_income:,.0f}\n"
        f"- Average structural damage ratio: {info.damage_ratio:.1%}\n"
        f"Focus on what the numbers mean for a typical resident. "
        f"Do not use em dashes. Keep it under 60 words."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
    )
    return {"summary": response.choices[0].message.content}


@app.get("/health")
async def health():
    return {"status": "ok", "openai_configured": client is not None}
