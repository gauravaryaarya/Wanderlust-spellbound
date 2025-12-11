import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import random

# Unique User Agent to prevent blocking
geolocator = Nominatim(user_agent="wanderlust_pro_v4_final", timeout=10)

@st.cache_data(ttl=3600)
def get_place_suggestions(user_input):
    if not user_input or len(user_input) < 3: return []
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': user_input, 'format': 'json', 'addressdetails': 1, 'limit': 5}
        headers = {'User-Agent': "wanderlust_pro_v4_final"}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        suggestions = []
        for item in response.json():
            if item.get('display_name') not in suggestions:
                suggestions.append(item.get('display_name'))
        return suggestions
    except:
        return []

@st.cache_data(ttl=3600)
def get_coordinates(place_name):
    try:
        location = geolocator.geocode(place_name)
        if location:
            return location.latitude, location.longitude
    except:
        pass
    return None

@st.cache_data(ttl=3600)
def get_trip_logistics(origin, destination):
    """
    Calculates Distance, Time, AND Estimated Travel Costs for different modes.
    """
    start_coords = get_coordinates(origin)
    end_coords = get_coordinates(destination)
    
    if not start_coords or not end_coords:
        return None

    # 1. Calculate Distance (Geodesic - accurate "crow flies", adding 20% for road curvature)
    dist_km = geodesic(start_coords, end_coords).km
    road_dist = int(dist_km * 1.2) 
    
    # 2. Estimate Costs (USD & INR)
    # Rates: Flight ~$0.15/km, Car ~$0.10/km, Train ~$0.04/km
    costs = {
        "flight": {"usd": int(dist_km * 0.12 + 50), "inr": int((dist_km * 0.12 + 50) * 84)},
        "car": {"usd": int(road_dist * 0.10), "inr": int((road_dist * 0.10) * 84)},
        "train": {"usd": int(road_dist * 0.04), "inr": int((road_dist * 0.04) * 84)},
        "bus": {"usd": int(road_dist * 0.03), "inr": int((road_dist * 0.03) * 84)}
    }
    
    # 3. Estimate Time
    times = {
        "flight": f"{int(dist_km/800 + 2)}h (Flight)", # +2h for airport time
        "car": f"{int(road_dist/70)}h {int((road_dist%70)/1.2)}m (Drive)",
        "train": f"{int(road_dist/80)}h (Train)"
    }

    return {
        "distance_km": road_dist,
        "coords": [start_coords, end_coords],
        "costs": costs,
        "times": times
    }