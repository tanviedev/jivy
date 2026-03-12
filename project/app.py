import sys
import os

# Ensure project root (HackX) is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation
import requests
from logic.insurance_engine import insurance_decision
LOCATION_MAP = {
    "Pune - Shivajinagar": (18.5308, 73.8475),
    "Pune - Kothrud": (18.5074, 73.8077),
    "Pune - Hadapsar": (18.5089, 73.9260),
    "Pune - Pimpri": (18.6298, 73.7997),
    "Pune - Viman Nagar": (18.5679, 73.9143)
}

# ================= SESSION STATE =================
if "recommendation" not in st.session_state:
    st.session_state.recommendation = None

if "selected_hospital" not in st.session_state:
    st.session_state.selected_hospital = None

# ---------------- PROJECT ROOT ----------------
from orchestrator import recommend_hospitals

# ================= PAGE CONFIG =================
st.set_page_config(page_title="JIVY", layout="wide")




st.title("🚑 JIVY – Urban Emergency Care Navigator (Pune)")

# ================= LOAD DATA =================
hospitals_master = pd.read_csv(os.path.join(BASE_DIR, "data", "Hospitals.csv"))
insurance_df = pd.read_csv(os.path.join(BASE_DIR, "data", "insurance.csv"))

# ================= LOCATION =================
st.subheader("📍 Your Location")

DEFAULT_LAT, DEFAULT_LON = 18.5204, 73.8567
lat, lon = DEFAULT_LAT, DEFAULT_LON

def get_user_location():
    loc = get_geolocation()
    if loc and "coords" in loc:
        return loc["coords"]["latitude"], loc["coords"]["longitude"]
    return None


use_gps = st.checkbox(
    "📡 Use live GPS location (recommended)",
    value=True
)

# ---------------- LIVE GPS (UNCHANGED) ----------------
if use_gps:
    gps = get_user_location()
    if gps:
        lat, lon = gps
        st.success("Live GPS location detected")
    else:
        st.warning("GPS unavailable — using fallback")

# ---------------- FALLBACK LOCATION MENU ----------------
if not use_gps or (lat, lon) == (DEFAULT_LAT, DEFAULT_LON):

    st.markdown("### 📍 Select Your Area (Fallback)")

    location_name = st.selectbox(
        "Choose a nearby location",
        options=list(LOCATION_MAP.keys())
    )

    if location_name:
        lat, lon = LOCATION_MAP[location_name]

    # OPTIONAL: manual override if user wants
    with st.expander("🔍 Enter area manually (optional)"):
        area = st.text_input("Enter your area")
        if area:
            geolocator = Nominatim(user_agent="jivy_app")
            location = geolocator.geocode(f"{area}, Pune, India")
            if location:
                lat, lon = location.latitude, location.longitude
            else:
                st.warning("Could not find location, using selected area")

# ---------------- FINAL USER LOCATION ----------------
user_location = (lat, lon)

# ================= ORS HELPER =================
ORS_API_KEY = st.secrets["ORS_API_KEY"]

def get_road_distance_and_route(start, end):
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [[start[1], start[0]], [end[1], end[0]]]
    }

    try:
        r = requests.post(url, json=body, headers=headers).json()
        feature = r["features"][0]
        distance_km = feature["properties"]["segments"][0]["distance"] / 1000
        duration_min = feature["properties"]["segments"][0]["duration"] / 60
        route = [(c[1], c[0]) for c in feature["geometry"]["coordinates"]]
        return round(distance_km, 2), int(duration_min), route
    except:
        return None, None, None

# ================= PATIENT INPUT =================
st.subheader("👤 Patient Details")

age = st.number_input("Age", 1, 100)

symptoms = st.multiselect(
    "🩺 Select Symptoms",
    ["Chest Pain", "Breathing Difficulty", "Fever", "Fracture", "Headache"]
)

policy = st.selectbox(
    "💳 Insurance Policy",
    ["No Insurance"] + sorted(insurance_df["policy_name"].unique())
)

# ================= EMERGENCY ACTION =================
st.divider()
st.subheader("🚨 Emergency Assessment")

if st.button("Get Recommendation"):
    if not symptoms:
        st.error("Please select at least one symptom.")
    else:
        risk, hospitals_rec = recommend_hospitals(
            age, symptoms, lat, lon, policy
        )
        st.session_state.recommendation = {
            "risk": risk,
            "hospitals": hospitals_rec
        }
        st.session_state.selected_hospital = None

# ================= SHOW RECOMMENDATION =================
if st.session_state.recommendation:
    risk = st.session_state.recommendation["risk"]
    hospitals_rec = st.session_state.recommendation["hospitals"]

    st.subheader("⚠️ Emergency Risk Level")
    st.error(risk)

    if hospitals_rec.empty:
        st.warning("No suitable hospitals found.")
    else:
        st.subheader("🏥 Recommended Hospitals (Select One)")

        # ---------- ROAD DISTANCE ENRICHMENT ----------
        enriched = []

        for _, row in hospitals_rec.iterrows():
            dist, eta, route = get_road_distance_and_route(
                user_location,
                (row["lat"], row["long"])
            )

            if dist is None:
                continue

            enriched.append({
                "name": row["name"],
                "hospital_type": row.get("hospital_type", "Unknown"),
                "lat": row["lat"],
                "long": row["long"],
                "road_km": dist,
                "eta_min": eta,
                "estimated_cost": row.get("estimated_cost", "N/A"),
                "insurance_status": row.get("insurance_status", "Unknown"),
                "route": route
            })

        if not enriched:
            st.error("⚠️ Could not calculate road distances. Check ORS API key or quota.")
            st.stop()

        road_df = (
            pd.DataFrame(enriched)
            .sort_values("road_km")
            .reset_index(drop=True)
        )

        # ---------- HOSPITAL CARDS ----------
        for i, row in road_df.iterrows():
            with st.container(border=True):
                st.markdown(f"### 🏥 {row['name']}")
                st.write(f"🚗 Distance: {row['road_km']} km")
                st.write(f"⏱ ETA: {row['eta_min']} minutes")
                st.write(f"💰 Estimated Cost: ₹{row['estimated_cost']}")
                st.write(f"💳 Insurance: {row['insurance_status']}")

                if st.button(f"🚑 Navigate to {row['name']}", key=f"nav_{i}"):
                    st.session_state.selected_hospital = row

                    insurance_result = insurance_decision(
                        user_id="u001",  # TEMP (later login)
                        selected_policy_name=policy,
                        hospital_name=row["name"],
                        estimated_cost=row["estimated_cost"],
                        requires_icu=(
                            "Chest Pain" in symptoms or
                            "Breathing Difficulty" in symptoms
                        )
                    )

                    st.session_state.insurance_result = insurance_result

        # ================= MAP =================
        st.subheader("🗺 Emergency Navigation Map")

        m = folium.Map(
            location=[lat, lon],
            zoom_start=13,
            tiles="OpenStreetMap"
        )

        # User
        folium.Marker(
            [lat, lon],
            popup="📍 Your Location",
            icon=folium.Icon(color="red", icon="user")
        ).add_to(m)

        # All hospitals
        for _, row in road_df.iterrows():
            folium.Marker(
                [row["lat"], row["long"]],
                popup=row["name"],
                icon=folium.Icon(color="blue", icon="plus-sign")
            ).add_to(m)

        # Selected hospital + highlighted route
        if st.session_state.selected_hospital is not None:
            sel = st.session_state.selected_hospital

            folium.Marker(
                [sel["lat"], sel["long"]],
                popup=f"✅ {sel['name']}",
                icon=folium.Icon(color="green", icon="star")
            ).add_to(m)

            # Background glow
            folium.PolyLine(
                sel["route"],
                color="#00BFFF",
                weight=12,
                opacity=0.5
            ).add_to(m)

            # Main route
            folium.PolyLine(
                sel["route"],
                color="red",
                weight=6,
                opacity=1
            ).add_to(m)

        st_folium(m, width=1000, height=500)
        st.error("🚑 Emergency Mode Active — proceed immediately")

# ================= INSURANCE RESULT =================
if "insurance_result" in st.session_state and st.session_state.insurance_result:
    result = st.session_state.insurance_result

    st.subheader("🧾 Insurance Eligibility")

    if result["status"] == "CASHLESS":
        st.success("✅ CASHLESS TREATMENT")
    elif result["status"] == "PARTIAL":
        st.warning("⚠️ PARTIAL COVERAGE")
    else:
        st.error("❌ OUT OF POCKET")

    st.caption(result["reason"])