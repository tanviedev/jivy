import os
from typing import List, Tuple

import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from project.orchestrator import recommend_hospitals
from logic.insurance_engine import insurance_decision


BASE_DIR = os.path.dirname(__file__)


class RecommendRequest(BaseModel):
    age: int
    symptoms: List[str]
    lat: float
    lon: float
    policy: str


class InsuranceRequest(BaseModel):
    user_id: str
    policy: str
    hospital_name: str
    estimated_cost: float
    requires_icu: bool


app = FastAPI(title="JIVY API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ORS_API_KEY = os.getenv("ORS_API_KEY")


def get_road_distance_and_route(
    start: Tuple[float, float],
    end: Tuple[float, float],
) -> Tuple[float | None, int | None, list[tuple[float, float]] | None]:
    """
    Wrapper around OpenRouteService, similar to the Streamlit app.
    """
    if not ORS_API_KEY:
        return None, None, None

    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "coordinates": [[start[1], start[0]], [end[1], end[0]]],
    }

    try:
        r = requests.post(url, json=body, headers=headers).json()
        feature = r["features"][0]
        distance_km = feature["properties"]["segments"][0]["distance"] / 1000
        duration_min = feature["properties"]["segments"][0]["duration"] / 60
        route = [(c[1], c[0]) for c in feature["geometry"]["coordinates"]]
        return round(distance_km, 2), int(duration_min), route
    except Exception:
        return None, None, None


@app.post("/api/recommend")
def api_recommend(req: RecommendRequest):
    """
    Returns risk level and enriched hospital list for the given patient context.
    """
    risk, hospitals_rec = recommend_hospitals(
        req.age,
        req.symptoms,
        req.lat,
        req.lon,
        req.policy,
    )

    if hospitals_rec.empty:
        return {"risk": risk, "hospitals": []}

    user_location = (req.lat, req.lon)

    enriched: list[dict] = []
    for _, row in hospitals_rec.iterrows():
        dist, eta, route = get_road_distance_and_route(
            user_location,
            (row["lat"], row["long"]),
        )

        enriched.append(
            {
                "name": row["name"],
                "hospital_type": row.get("hospital_type", "Unknown"),
                "lat": float(row["lat"]),
                "long": float(row["long"]),
                "straight_line_km": float(row.get("distance_km", 0.0)),
                "road_km": dist,
                "eta_min": eta,
                "estimated_cost": float(row.get("estimated_cost", 0.0)),
                "insurance_status": str(row.get("insurance_status", "Unknown")),
                "route": route,
            }
        )

    return {"risk": risk, "hospitals": enriched}


@app.post("/api/insurance")
def api_insurance(req: InsuranceRequest):
    """
    Runs the insurance eligibility engine for a chosen hospital.
    """
    decision = insurance_decision(
        user_id=req.user_id,
        selected_policy_name=req.policy,
        hospital_name=req.hospital_name,
        estimated_cost=req.estimated_cost,
        requires_icu=req.requires_icu,
    )
    return decision

