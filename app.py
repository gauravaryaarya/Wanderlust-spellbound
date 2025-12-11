import streamlit as st
from datetime import date
from src.ai_engine import configure_genai, generate_itinerary, ask_travel_bot
from src.map_engine import plot_itinerary_map
from streamlit_folium import st_folium

# Page Config
st.set_page_config(page_title="Wanderlust AI", layout="wide", page_icon="✈️")

# Custom CSS for "Cinematic" feel
st.markdown("""
<style>
    .main {background-color: #0e1117;}
    h1 {color: #FF4B4B;}
    .stButton>button {width: 100%; border-radius: 20px;}
</style>
""", unsafe_allow_html=True)

# Sidebar Inputs [cite: 266]
with st.sidebar:
    st.title("🌍 Plan Your Journey")
    destination = st.text_input("Destination", "Paris, France")
    start_date = st.date_input("Start Date", date.today())
    duration = st.slider("Duration (Days)", 1, 14, 3)
    budget = st.select_slider("Budget", options=["Budget", "Mid-Range", "Luxury"])
    travelers = st.selectbox("Travelers", ["Solo", "Couple", "Family", "Friends"])
    interests = st.multiselect("Interests", ["History", "Food", "Adventure", "Relaxation", "Art"], ["Food", "Adventure"])
    
    generate_btn = st.button("Generate Itinerary 🚀")

# Main Area
st.title("✈️ Wanderlust AI: Smart Travel Planner")
st.caption("Powered by Gemini Flash • Live Mapping • Smart Agent")

if generate_btn:
    with st.spinner("Consulting the Travel Agent..."):
        configure_genai() # Ensure API key is loaded
        
        # 1. Generate Plan
        trip_data = generate_itinerary(destination, start_date, duration, budget, travelers, interests)
        
        if "error" in trip_data:
            st.error("AI Error: " + trip_data['error'])
        else:
            # Store in session state to persist
            st.session_state['trip_data'] = trip_data
            st.success("Itinerary Generated!")

# Display Logic
if 'trip_data' in st.session_state:
    data = st.session_state['trip_data']
    
    # Header
    st.header(data.get('trip_title', f"Trip to {destination}"))
    st.info(data.get('summary', ''))
    
    # 2. Map Section 
    st.subheader("📍 Your Route")
    map_obj = plot_itinerary_map(data)
    st_folium(map_obj, width=800, height=400)
    
    # 3. Day-by-Day Itinerary [cite: 269]
    for day in data.get('days', []):
        with st.expander(f"Day {day['day']}: {day.get('date', '')}", expanded=True):
            for act in day['activities']:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.badge(act.get('time', ''))
                with col2:
                    st.markdown(f"**{act['activity']}**")
                    st.write(act['description'])
                    st.caption(f"💰 {act.get('cost', 'N/A')}")
    
    # 4. Recommendations [cite: 275]
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏨 Hotels")
        for hotel in data.get('hotel_recommendations', []):
            st.success(hotel)
    with col_b:
        st.subheader("🍽️ Dining")
        for food in data.get('dining_recommendations', []):
            st.warning(food)

    # 5. AI Chatbot (Bonus Feature) [cite: 288]
    st.divider()
    st.subheader("🤖 Ask the Travel Bot")
    user_q = st.text_input("Ask about transport, weather, or specific food spots:")
    if user_q:
        with st.spinner("Thinking..."):
            # Simple stateless chat for MVP, can pass history if needed
            answer = ask_travel_bot([], f"Context: {str(data)}. Question: {user_q}")
            st.markdown(f"**AI:** {answer}")