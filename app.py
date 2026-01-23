import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests

# ========== CONFIG ==========
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNjMjFlNzAxMGU0NzRiYjBhOGNjNTMyYmIwOGY1N2Y0IiwiaCI6Im11cm11cjY0In0="  # the one you copied from dashboard

# ========== LOAD DATA ==========
hospitals = pd.read_csv("data/Hospitals.csv")

st.set_page_config(page_title="JIVY")
st.title("JIVY – Urban Emergency Care Navigator (Pune)")

# ========== USER LOCATION ==========
area = st.text_input("Enter your Area (e.g., Kothrud, Hinjewadi, Shivajinagar)")

lat, lon = 18.5204, 73.8567
geolocator = Nominatim(user_agent="jivy_app")

if area:
    location = geolocator.geocode(area + ", Pune, India")
    if location:
        lat, lon = location.latitude, location.longitude
        st.success(f"Location found: {area}")
    else:
        st.error("Area not found. Showing Pune center.")

user_location = (lat, lon)

# ========== DISTANCE CALCULATION ==========
hospitals["distance_km"] = hospitals.apply(
    lambda row: geodesic(user_location, (row["lat"], row["long"])).km,
    axis=1
)

nearest_hospitals = hospitals.sort_values("distance_km").head(5)

# ========== HOSPITAL SELECTION ==========
st.subheader("Recommended Nearby Hospitals")
selected_hospital = st.selectbox("Select Hospital", nearest_hospitals["name"])

selected_row = nearest_hospitals[nearest_hospitals["name"] == selected_hospital].iloc[0]
hosp_lat, hosp_lon = selected_row["lat"], selected_row["long"]

# ========== ROUTING FUNCTION ==========
def get_route(start, end):
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [
            [start[1], start[0]],
            [end[1], end[0]]
        ]
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    if "features" not in data:
        st.error("Routing API failed.")
        st.json(data)
        return [(start[0], start[1]), (end[0], end[1])]

    coords = data["features"][0]["geometry"]["coordinates"]
    return [(c[1], c[0]) for c in coords]

route_points = get_route((lat, lon), (hosp_lat, hosp_lon))

# ========== MAP ==========
m = folium.Map(location=[lat, lon], zoom_start=13)

# User marker
folium.Marker([lat, lon], popup="Your Location", icon=folium.Icon(color="red")).add_to(m)

# Nearby hospital markers
for _, row in nearest_hospitals.iterrows():
    folium.Marker(
        [row["lat"], row["long"]],
        popup=row["name"],
        icon=folium.Icon(color="blue")
    ).add_to(m)

# Selected hospital marker
folium.Marker(
    [hosp_lat, hosp_lon],
    popup=selected_hospital,
    icon=folium.Icon(color="green")
).add_to(m)

# Real road route
folium.PolyLine(route_points, color="blue", weight=5).add_to(m)

st.subheader("Emergency Navigation Map")
st_folium(m, width=700, height=500)

# ========== EMERGENCY FLOW ==========
if st.button("Check Risk"):
    st.subheader("Risk Level")
    st.write("High (Demo)")

    st.error("🚨 Emergency Mode Activated")
    st.write(f"Proceed immediately to: {selected_hospital}")
