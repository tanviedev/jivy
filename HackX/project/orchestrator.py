import sys
import os
import pandas as pd

# -------------------------------------------------
# Ensure project root is visible
# -------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# Imports
# -------------------------------------------------
from ml.risk_model import predict_risk
from logic.hospital_filter import filter_hospitals
from logic.cost_logic import attach_costs
from logic.insurance_logic import attach_insurance
from logic.scoring import rank_hospitals
from utils.geo import compute_distance

# -------------------------------------------------
# Load DATA explicitly (GLOBAL, ONCE)
# -------------------------------------------------
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

HOSPITALS = pd.read_csv(os.path.join(DATA_DIR, "clean_pune_hospitals.csv"))
COSTS = pd.read_csv(os.path.join(DATA_DIR, "costs.csv"))
INSURANCE = pd.read_csv(os.path.join(DATA_DIR, "insurance.csv"))
HOSP_INS = pd.read_csv(os.path.join(DATA_DIR, "hospitals_with_insurance.csv"))

# -------------------------------------------------
# MAIN PIPELINE FUNCTION
# -------------------------------------------------
def recommend_hospitals(age, symptoms, user_lat, user_long, policy):
    """
    ALWAYS returns at least one recommendation.
    """

    # 1. Risk assessment
    risk = predict_risk(age, symptoms)

    # 2. Risk-based filtering
    filtered = filter_hospitals(HOSPITALS, risk)

    # 3. Absolute safety fallback
    if filtered.empty:
        filtered = HOSPITALS.copy()

    # 4. Distance calculation
    filtered = filtered.copy()
    filtered["distance_km"] = [
        compute_distance(user_lat, user_long, lat, lon)
        for lat, lon in zip(filtered["lat"], filtered["long"])
    ]

    # 5. Cost & insurance
    filtered = attach_costs(filtered, COSTS, symptoms)
    filtered = attach_insurance(filtered, policy, INSURANCE, HOSP_INS, None)

    # 6. Hospital type (human-readable)
    def classify_hospital(row):
        if row["facility_type"] in ["Clinic", "Dispensary"]:
            return "Clinic"
        if row["ownership"] == "Government":
            return "Government Hospital"
        return "Private Hospital"

    filtered["hospital_type"] = filtered.apply(classify_hospital, axis=1)

    # 7. Ranking
    ranked = rank_hospitals(filtered, risk)

    # 8. FINAL GUARANTEE
    if ranked.empty:
        ranked = filtered.sort_values("distance_km").head(5)

    return risk, ranked
