import sys
import os
import streamlit as st
import pandas as pd

# ---------------- LOCATION MAP ----------------
LOCATION_MAP = {
    "Pune - Shivajinagar": (18.5308, 73.8475),
    "Pune - Kothrud": (18.5074, 73.8077),
    "Pune - Hadapsar": (18.5089, 73.9260),
    "Pune - Pimpri": (18.6298, 73.7997),
    "Pune - Viman Nagar": (18.5679, 73.9143)
}

# ---------------- PROJECT ROOT SETUP ----------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from orchestrator import recommend_hospitals

# ---------------- UI ----------------
st.title("Urban Healthcare Navigator")

age = st.number_input("Age", 1, 100)

symptoms = st.multiselect(
    "Select Symptoms",
    ["Chest Pain", "Breathing Difficulty", "Fever", "Fracture", "Headache"]
)

location_name = st.selectbox(
    "Select Your Area",
    options=list(LOCATION_MAP.keys())
)

user_lat, user_long = LOCATION_MAP[location_name]

# ---------------- INSURANCE ----------------
insurance_df = pd.read_csv("data/insurance.csv")
policy_options = sorted(insurance_df["policy_name"].unique().tolist())

policy = st.selectbox(
    "Select Insurance Policy",
    options=["No Insurance"] + policy_options
)

# ---------------- ACTION ----------------
if st.button("Get Recommendation"):
    if not symptoms:
        st.error("Please select at least one symptom.")
    else:
        risk, hospitals = recommend_hospitals(
            age, symptoms, user_lat, user_long, policy
        )

        st.subheader(f"Emergency Risk: {risk}")

        if hospitals.empty:
            st.warning("No suitable hospitals found for the selected symptoms.")
        else:
            desired_cols = [
                "name",
                "hospital_type",
                "distance_km",
                "estimated_cost",
                "insurance_status"
            ]

            available_cols = [c for c in desired_cols if c in hospitals.columns]
            st.dataframe(hospitals[available_cols])
