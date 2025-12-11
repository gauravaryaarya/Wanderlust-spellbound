import streamlit as st
import streamlit.components.v1 as components
import time
import json
from datetime import date
from src.ai_engine import configure_genai, generate_itinerary, ask_travel_bot
from src.navigation import get_route_metrics, get_place_suggestions
from src.db import init_db, add_user, check_login, save_trip, get_history, update_note

# --- CONFIG & INIT ---
st.set_page_config(page_title="Wanderlust AI", layout="wide", page_icon="✈️")
init_db()

# Custom CSS for that "Cinematic" Dark Mode
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    .title-animate {
        font-size: 80px; font-weight: bold; text-align: center;
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeIn 3s;
    }
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    .success-box {padding: 1rem; background-color: #1c1f26; border-radius: 10px; border-left: 5px solid #4CAF50;}
    .history-card {padding: 10px; border: 1px solid #333; margin-bottom: 10px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'splash' # Start with Splash
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- PAGE 1: SPLASH SCREEN ---
if st.session_state['page'] == 'splash':
    empty_spot = st.empty()
    
    with empty_spot.container():
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="title-animate">WANDERLUST AI</p>', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: gray;'>The World Awaits.</h3>", unsafe_allow_html=True)
    
    time.sleep(2.5) # Wait for animation
    empty_spot.empty() # Clear screen
    st.session_state['page'] = 'login' # Go to Login
    st.rerun()

# --- PAGE 2: AUTHENTICATION ---
elif st.session_state['page'] == 'login':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("✈️ Welcome Back")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Log In", type="primary"):
                if check_login(username, password):
                    st.session_state['user'] = username
                    st.session_state['page'] = 'home'
                    st.toast(f"Welcome back, {username}!", icon="👋")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with tab2:
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                if add_user(new_user, new_pass):
                    st.success("Account created! Please log in.")
                else:
                    st.error("Username already exists.")

# --- PAGE 3: MAIN DASHBOARD ---
elif st.session_state['page'] == 'home':
    
    # --- SIDEBAR (HISTORY & LOGOUT) ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state['user']}**")
        if st.button("Log Out"):
            st.session_state['user'] = None
            st.session_state['page'] = 'login'
            st.rerun()
        
        st.divider()
        st.subheader("📜 Travel History")
        history = get_history(st.session_state['user'])
        
        if not history:
            st.caption("No past trips yet.")
        
        for row in history:
            trip_id, dest, data_json, notes, date_created = row
            with st.expander(f"{dest} ({date_created[:10]})"):
                # Load old trip data back into view
                if st.button(f"Load Plan #{trip_id}"):
                    st.session_state['trip_data'] = json.loads(data_json)
                    st.rerun()
                
                # Notes Section
                st.markdown("**📝 Notes:**")
                new_note = st.text_area("Edit Note", value=notes, key=f"note_{trip_id}", height=70)
                if st.button("Save Note", key=f"save_{trip_id}"):
                    update_note(trip_id, new_note)
                    st.toast("Note saved!")

    # --- MAIN CONTENT ---
    st.title("🌍 Plan Your Next Adventure")
    
    # 1. USER INPUT FORM (First thing on Home)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            raw_origin = st.text_input("From", placeholder="Current City", key="origin")
            # Smart Suggestion Logic
            if raw_origin:
                sug = get_place_suggestions(raw_origin)
                final_origin = st.selectbox("Confirm Origin", sug, index=0) if sug else raw_origin
            else:
                final_origin = None

        with c2:
            raw_dest = st.text_input("To", placeholder="Dream Destination", key="dest")
            if raw_dest:
                sug = get_place_suggestions(raw_dest)
                final_dest = st.selectbox("Confirm Destination", sug, index=0) if sug else raw_dest
            else:
                final_dest = None

        c3, c4, c5 = st.columns(3)
        with c3:
            start_date = st.date_input("When?", date.today())
        with c4:
            duration = st.slider("Days", 1, 15, 3)
        with c5:
            budget = st.select_slider("Budget", ["Budget", "Mid-Range", "Luxury"], value="Mid-Range")
        
        interests = st.multiselect("Interests", ["Food", "History", "Nature", "Adventure"], ["Food"])
        
        if st.button("🚀 Generate Journey", type="primary", use_container_width=True):
            if final_dest:
                with st.spinner("Analyzing routes, prices, and hidden gems..."):
                    configure_genai()
                    trip_data = generate_itinerary(final_dest, start_date, duration, budget, "Solo", interests)
                    
                    if "error" not in trip_data:
                        # SAVE TO DB AUTOMATICALLY
                        save_trip(st.session_state['user'], final_dest, trip_data)
                        st.session_state['trip_data'] = trip_data
                        st.rerun() # Refresh to show data
                    else:
                        st.error(trip_data['error'])

    # 2. DISPLAY RESULTS (Only if data exists)
    if 'trip_data' in st.session_state:
        data = st.session_state['trip_data']
        
        st.divider()
        
        # A) LOCATION VISUALIZATION (Map)
        if final_origin and final_dest:
             st.subheader(f"🗺️ Route Visualization: {final_origin} ➝ {final_dest}")
             map_url = f"https://maps.google.com/maps?saddr={final_origin.replace(' ','+')}&daddr={final_dest.replace(' ','+')}&output=embed"
             components.iframe(src=map_url, height=400)
        
        # B) AI ITINERARY
        st.subheader(f"📅 Your {duration}-Day Itinerary for {data.get('trip_title', 'Trip')}")
        for day in data.get('days', []):
            with st.expander(f"Day {day['day']}", expanded=True):
                for act in day['activities']:
                    col_a, col_b = st.columns([1, 4])
                    col_a.markdown(f"**{act.get('time')}**")
                    col_b.markdown(f"**{act.get('activity')}** - {act.get('description')}")
        
        # C) RECOMMENDATIONS (Hotels, Food, Safety)
        st.subheader("💎 Smart Recommendations")
        tab1, tab2, tab3 = st.tabs(["🏨 Hotels", "🍽️ Restaurants", "🛡️ Safety Tips"])
        
        with tab1:
            for h in data.get('hotel_recommendations', []):
                st.success(h)
        with tab2:
            for f in data.get('dining_recommendations', []):
                st.info(f)
        with tab3:
            st.warning(data.get('safety_tips', "Stay safe and follow local guidelines."))