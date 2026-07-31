from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os

app = FastAPI(
    title="Agro Mitra Backend API",
    description="Backend services for Agro Mitra Smart Farming Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGMARKNET_API_KEY = os.getenv("AGMARKNET_API_KEY", "579b464db66ec23bdd0000016c66024377e5447a50194060e6a70d9c")

@app.get("/")
def read_root():
    return {"message": "Welcome to Agro Mitra API", "status": "online"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/weather")
async def get_weather(lat: float = 31.6340, lon: float = 74.8723):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&hourly=precipitation_probability&timezone=auto"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            curr = data.get("current", {})
            return {
                "temperature": curr.get("temperature_2m", 28),
                "humidity": curr.get("relative_humidity_2m", 64),
                "wind_speed": curr.get("wind_speed_10m", 12.0),
                "weather_code": curr.get("weather_code", 0),
                "condition": "Partly Cloudy"
            }
        except Exception as e:
            return {
                "temperature": 28,
                "humidity": 64,
                "wind_speed": 12.0,
                "condition": "Partly Cloudy",
                "error": str(e)
            }

@app.get("/api/v1/marketplace/prices")
async def get_mandi_prices(state: Optional[str] = "Punjab"):
    # Real Agmarknet API endpoint integration with data.gov.in key
    agmarknet_url = f"https://api.data.gov.in/resource/9ef0be34-55f4-4115-a6a1-4af09a903b36?api-key={AGMARKNET_API_KEY}&format=json&offset=0&limit=10"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(agmarknet_url)
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                if records:
                    return [
                        {
                            "commodity": r.get("commodity", "Wheat"),
                            "mandi": r.get("market", "Amritsar"),
                            "price": int(float(r.get("modal_price", 2275))),
                            "change": 1.2,
                            "unit": "quintal"
                        }
                        for r in records[:5]
                    ]
        except Exception:
            pass

    # Fallback mandi data
    return [
        {"commodity": "Basmati Rice", "mandi": "Amritsar", "price": 3850, "change": 2.5, "unit": "quintal"},
        {"commodity": "Wheat", "mandi": "Ludhiana", "price": 2275, "change": -0.8, "unit": "quintal"},
        {"commodity": "Maize", "mandi": "Patiala", "price": 1980, "change": 1.2, "unit": "quintal"},
        {"commodity": "Tomato", "mandi": "Delhi", "price": 2400, "change": 8.5, "unit": "quintal"},
    ]

class CropReq(BaseModel):
    soil_type: str
    season: str
    state: str

@app.post("/api/v1/crops/recommend")
def recommend_crops(req: CropReq):
    return {
        "soil_type": req.soil_type,
        "season": req.season,
        "recommendations": [
            {
                "rank": 1,
                "name": "Basmati Rice",
                "variety": "Pusa Basmati 1121",
                "suitability": 0.95,
                "yield": "35-40 q/ha",
                "reason": f"Highly suitable for {req.soil_type} soil during {req.season} in {req.state}."
            },
            {
                "rank": 2,
                "name": "Maize",
                "variety": "DHM 117",
                "suitability": 0.88,
                "yield": "50-60 q/ha",
                "reason": "Excellent water efficiency and high market demand."
            }
        ]
    }
