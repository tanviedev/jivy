import os
from typing import List, Tuple

import pandas as pd

from utils.geo import compute_distance
from ml.risk_model import predict_risk
from logic.symptom_map import get_required_specializations
from logic.hospital_filter import filter_hospitals
from logic.cost_logic import attach_costs
from logic.insurance_logic import attach_insurance
from logic.scoring import rank_hospitals


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _load_hospitals() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "Hospitals.csv")
    df = pd.read_csv(path)

    # Normalize key columns we rely on downstream
    df = df.rename(
        columns={
            "facility_type": "facility_type",
            "ownership": "ownership",
        }
    )

    # Ensure numeric lat/long
    df["lat"] = df["lat"].astype(float)
    df["long"] = df["long"].astype(float)

    return df


_HOSPITALS_MASTER = _load_hospitals()


def recommend_hospitals(
    age: int,
    symptoms: List[str],
    user_lat: float,
    user_long: float,
    policy: str,
) -> Tuple[str, pd.DataFrame]:
    """
    Main orchestration function used by the Streamlit UI.

    Returns:
        risk_level (str): "High" / "Medium" / "Low"
        hospitals (pd.DataFrame): ranked hospitals with at least
            columns: name, lat, long, hospital_type,
            estimated_cost, insurance_status, distance_km.
    """

    df = _HOSPITALS_MASTER.copy()

    # 1️⃣ Risk assessment
    risk_level = predict_risk(age, symptoms or [])

    # 2️⃣ Compute straight-line distance from user
    df["distance_km"] = df.apply(
        lambda row: compute_distance(
            user_lat,
            user_long,
            row["lat"],
            row["long"],
        ),
        axis=1,
    )

    # 3️⃣ Filter hospitals based on risk level
    df = filter_hospitals(df, risk_level)

    # 4️⃣ Attach rough treatment costs based on symptoms
    costs_path = os.path.join(DATA_DIR, "costs.csv")
    cost_df = pd.read_csv(costs_path)
    df = attach_costs(df, cost_df, symptoms or [])

    # 5️⃣ Attach simple insurance preference score
    insurance_df = pd.read_csv(os.path.join(DATA_DIR, "insurance.csv"))
    df = attach_insurance(
        df,
        policy,
        insurance_df,
        hosp_ins_df=None,
        condition=None,
    )

    # 6️⃣ Rank and pick top candidates
    ranked = rank_hospitals(df, risk_level)

    # 7️⃣ Align column names with what the Streamlit app expects
    if "facility_type" in ranked.columns:
        ranked["hospital_type"] = ranked["facility_type"]

    # Ensure required columns exist even if missing in raw data
    for col in ["estimated_cost", "insurance_status"]:
        if col not in ranked.columns:
            ranked[col] = "N/A"

    return risk_level, ranked

