import folium
from streamlit_folium import st_folium

def plot_itinerary_map(itinerary_json):
    # Default to a central location if data is missing
    m = folium.Map(location=[20, 0], zoom_start=2)
    
    locations = []
    
    if "days" in itinerary_json:
        for day in itinerary_json['days']:
            for activity in day['activities']:
                loc_str = activity.get('location', '')
                try:
                    # Parse "Lat,Lon" string
                    if "," in loc_str:
                        lat, lon = map(float, loc_str.split(','))
                        folium.Marker(
                            [lat, lon],
                            popup=f"Day {day['day']}: {activity['activity']}",
                            tooltip=activity['activity'],
                            icon=folium.Icon(color="blue", icon="info-sign")
                        ).add_to(m)
                        locations.append([lat, lon])
                except:
                    continue

    # Auto-zoom to fit markers
    if locations:
        m.fit_bounds(locations)
    
    return m