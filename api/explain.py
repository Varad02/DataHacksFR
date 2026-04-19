"""OpenAI-powered neighborhood risk explainer (FastAPI endpoint)."""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from openai import OpenAIError
from openai import RateLimitError

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


def _local_summary(info: TractInfo) -> str:
    risk_band = "moderate"
    if info.damage_ratio >= 0.15 or info.mean_loss_per_household >= 120000:
        risk_band = "high"
    elif info.damage_ratio <= 0.03 and info.mean_loss_per_household <= 20000:
        risk_band = "lower"

    burden = 0.0
    if info.median_income > 0:
        burden = info.mean_loss_per_household / info.median_income

    burden_note = ""
    if burden >= 0.5:
        burden_note = " The expected loss is a large fraction of annual household income."
    elif burden >= 0.2:
        burden_note = " The expected loss is a meaningful share of annual household income."

    return (
        f"{info.name or info.tract} shows {risk_band} earthquake risk. "
        f"Typical modeled loss is about ${info.mean_loss_per_household:,.0f} per household, "
        f"with average damage near {info.damage_ratio:.1%}.{burden_note}"
    )


@app.post("/api/explain")
async def explain(info: TractInfo) -> dict:
    if client is None:
        return {"summary": _local_summary(info), "source": "local-fallback"}

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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        return {"summary": response.choices[0].message.content, "source": "openai"}
    except (RateLimitError, OpenAIError):
        return {"summary": _local_summary(info), "source": "local-fallback"}


@app.get("/health")
async def health():
    return {"status": "ok", "openai_configured": client is not None}
