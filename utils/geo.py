from geopy.distance import geodesic

def compute_distance(user_lat, user_long, hosp_lat, hosp_long):
    return float(
        geodesic(
            (float(user_lat), float(user_long)),
            (float(hosp_lat), float(hosp_long))
        ).km
    )
