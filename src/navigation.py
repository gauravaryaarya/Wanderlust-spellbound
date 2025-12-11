import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Unique user agent
geolocator = Nominatim(user_agent="wanderlust_pro_v8_final", timeout=10)

@st.cache_data(ttl=3600)
def get_place_suggestions(user_input):
    if not user_input or len(user_input) < 3: return []
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': user_input, 'format': 'json', 'addressdetails': 1, 'limit': 5}
        headers = {'User-Agent': "wanderlust_pro_v8_final"}
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
    # Realistic cost per KM estimates
    flight_inr = 4000 + (dist_km * 10)
    train_inr = 500 + (dist_km * 2)
    bus_inr = 300 + (dist_km * 3)
    car_inr = 2000 + (dist_km * 12)

    return {
        "flight": {"inr": int(flight_inr), "usd": int(flight_inr / 84)},
        "train": {"inr": int(train_inr), "usd": int(train_inr / 84)},
        "bus": {"inr": int(bus_inr), "usd": int(bus_inr / 84)},
        "car": {"inr": int(car_inr), "usd": int(car_inr / 84)}
    }

@st.cache_data(ttl=3600)
def get_trip_logistics(origin, destination):
    c1 = get_coordinates(origin)
    c2 = get_coordinates(destination)
    
    if not c1 or not c2: return None

    # Guaranteed Distance
    dist_km = int(geodesic(c1, c2).km)
    
    # Guaranteed Time
    flight_time = f"{max(1, int(dist_km/800)+2)}h"
    train_time = f"{max(1, int(dist_km/70))}h"
    drive_time = f"{int(dist_km/60)}h"

    # Guaranteed Cost
    costs = calculate_costs(dist_km)

    return {
        "distance_km": dist_km,
        "costs": costs,
        "times": {"flight": flight_time, "train": train_time, "car": drive_time}
    }