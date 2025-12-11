import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import math

# Unique user agent to prevent blocking
geolocator = Nominatim(user_agent="wanderlust_final_pro_v7", timeout=10)

@st.cache_data(ttl=3600)
def get_place_suggestions(user_input):
    if not user_input or len(user_input) < 3: return []
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': user_input, 'format': 'json', 'addressdetails': 1, 'limit': 5}
        headers = {'User-Agent': "wanderlust_final_pro_v7"}
        res = requests.get(url, params=params, headers=headers, timeout=2)
        return [i.get('display_name') for i in res.json()]
    except:
        return []

@st.cache_data(ttl=3600)
def get_coordinates(place_name):
    try:
        loc = geolocator.geocode(place_name)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return None

def calculate_costs(dist_km):
    """
    Returns realistic costs based on distance logic.
    """
    # Base rates: Fixed base price + Cost per KM
    flight_usd = 80 + (dist_km * 0.12)
    train_usd = 15 + (dist_km * 0.05)
    bus_usd = 10 + (dist_km * 0.03)
    car_usd = 40 + (dist_km * 0.15) 

    return {
        "flight": {"usd": int(flight_usd), "inr": int(flight_usd * 84)},
        "train": {"usd": int(train_usd), "inr": int(train_usd * 84)},
        "bus": {"usd": int(bus_usd), "inr": int(bus_usd * 84)},
        "car": {"usd": int(car_usd), "inr": int(car_usd * 84)}
    }

@st.cache_data(ttl=3600)
def get_trip_logistics(origin, destination):
    c1 = get_coordinates(origin)
    c2 = get_coordinates(destination)
    
    if not c1 or not c2:
        return None

    # 1. Distance Calculation (Guaranteed)
    dist_km = int(geodesic(c1, c2).km)
    
    # 2. Travel Time Estimates
    flight_time = f"{max(1, int(dist_km/800)+2)}h"
    train_time = f"{max(1, int(dist_km/70))}h"
    drive_time = f"{int(dist_km/60)}h"

    # 3. Cost Calculation
    costs = calculate_costs(dist_km)

    return {
        "distance_km": dist_km,
        "costs": costs,
        "times": {
            "flight": flight_time,
            "train": train_time,
            "car": drive_time
        }
    }