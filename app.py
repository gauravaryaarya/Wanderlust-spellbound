import streamlit as st
import streamlit.components.v1 as components
import time
import json
import re
from datetime import date
from src.ai_engine import configure_genai, generate_itinerary, ask_travel_bot
from src.navigation import get_trip_logistics, get_place_suggestions
from src.db import init_db, add_user, check_login, save_trip, get_history, update_note

st.set_page_config(page_title="Wanderlust AI", layout="wide", page_icon="✈️")
init_db()

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
    .transport-card {
        border: 1px solid #444; border-radius: 8px; padding: 10px; margin: 5px; background: #222; text-align: center;
    }
    .cost-card {
        background-color: #1c1f26; border: 1px solid #4CAF50; padding: 15px; border-radius: 10px; text-align: center;
    }
    .cost-card.over-budget { border-color: #FF4B4B; background-color: #2d1b1b; }
    iframe {border-radius: 10px; border: 1px solid #333;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton button {width: 100%;}
</style>
""", unsafe_allow_html=True)

def parse_cost(cost_str):
    if not cost_str: return 0
    match = re.search(r"₹([\d,]+)", str(cost_str))
    if match: return int(match.group(1).replace(",", ""))
    return 0

# --- AUTH ---
if 'user' not in st.session_state:
    if "user" in st.query_params:
        st.session_state['user'] = st.query_params["user"]
        st.session_state['page'] = 'home'
    else:
        st.session_state['user'] = None
        st.session_state['page'] = 'splash'

# --- SPLASH ---
if st.session_state['page'] == 'splash':
    empty = st.empty()
    with empty.container():
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="title-animate">WANDERLUST AI</p>', unsafe_allow_html=True)
    time.sleep(2)
    empty.empty()
    st.session_state['page'] = 'login'
    st.rerun()

# --- LOGIN ---
elif st.session_state['page'] == 'login':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("✈️ Login")
        tab1, tab2 = st.tabs(["Sign In", "Register"])
        with tab1:
            u = st.text_input("User")
            p = st.text_input("Pass", type="password")
            if st.button("Go", type="primary"):
                if check_login(u, p):
                    st.session_state['user'] = u
                    st.session_state['page'] = 'home'
                    st.query_params["user"] = u
                    st.rerun()
                else: st.error("Fail")
        with tab2:
            nu = st.text_input("New User")
            np = st.text_input("New Pass", type="password")
            if st.button("Create"):
                if add_user(nu, np): st.success("Created!")
                else: st.error("Taken")

# --- HOME ---
elif st.session_state['page'] == 'home':
    with st.sidebar:
        st.title(f"👤 {st.session_state['user']}")
        if st.button("Log Out"):
            st.session_state['user'] = None
            st.session_state['page'] = 'login'
            st.query_params.clear()
            st.rerun()
        st.divider()
        st.subheader("📜 History")
        for row in get_history(st.session_state['user']):
            tid, dest, djson, note, date_c = row
            with st.expander(f"{dest}"):
                if st.button("Load", key=f"l_{tid}"):
                    st.session_state['trip_data'] = json.loads(djson)
                    st.rerun()

    st.title("🌍 Plan Your Next Adventure")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ro = st.text_input("From", key="o")
            fo = st.selectbox("Confirm", get_place_suggestions(ro), index=0) if ro and get_place_suggestions(ro) else ro
        with c2:
            rd = st.text_input("To", key="d")
            fd = st.selectbox("Confirm", get_place_suggestions(rd), index=0) if rd and get_place_suggestions(rd) else rd
            
        c3, c4, c5 = st.columns(3)
        sd = c3.date_input("Start")
        dur = c4.slider("Days", 1, 10, 3)
        bud_type = c5.select_slider("Style", ["Cheap", "Mid", "Lux"], value="Mid")
        
        c6, c7, c8 = st.columns(3)
        # NEW: TRAVELERS & TRIP TYPE
        travelers = c6.number_input("Travelers", min_value=1, max_value=20, value=1)
        trip_type = c7.selectbox("Trip Type", ["Solo", "Couple", "Family", "Friends", "Business"])
        max_budget = c8.number_input("Max Total Budget (₹)", 5000, 1000000, 20000, 1000)
        
        # EXPANDED INTERESTS
        intr = st.multiselect("Interests", 
                              ["Food", "Nature", "History", "Adventure", "Shopping", 
                               "Nightlife", "Art & Museums", "Relaxation", "Hidden Gems", 
                               "Photography", "Wellness & Spa", "Local Culture"], 
                              ["Food", "Nature"])
        
        if st.button("🚀 Generate Journey", type="primary"):
            if fd and fo:
                with st.spinner("Analyzing routes & generating plan..."):
                    configure_genai()
                    st.session_state['selected_activities'] = {}
                    # Pass new params to AI
                    trip_data = generate_itinerary(fd, sd, dur, bud_type, max_budget, travelers, trip_type, intr)
                    logistics = get_trip_logistics(fo, fd)
                    
                    if "error" not in trip_data:
                        save_trip(st.session_state['user'], fd, trip_data)
                        st.session_state['trip_data'] = trip_data
                        st.session_state['logistics'] = logistics
                        st.session_state['travelers_count'] = travelers # Save for display
                        st.rerun()
                    else: st.error(trip_data['error'])

    # --- RESULTS ---
    if 'trip_data' in st.session_state:
        data = st.session_state['trip_data']
        logistics = st.session_state.get('logistics')
        travelers_count = st.session_state.get('travelers_count', 1)
        
        st.divider()
        st.header(data.get('trip_title', f"Trip to {fd}"))
        
        # LOGISTICS PANEL
        if logistics:
            st.subheader("✈️ Travel Estimates (One-Way)")
            lc1, lc2, lc3, lc4 = st.columns(4)
            # Display logic: Flights/Train usually per person, Car total.
            with lc1: st.markdown(f"<div class='transport-card'>✈️ <b>Flight</b><br>₹{logistics['costs']['flight']['inr']:,}<br><small>{logistics['times']['flight']} (Per Person)</small></div>", unsafe_allow_html=True)
            with lc2: st.markdown(f"<div class='transport-card'>🚆 <b>Train</b><br>₹{logistics['costs']['train']['inr']:,}<br><small>{logistics['times']['train']} (Per Person)</small></div>", unsafe_allow_html=True)
            with lc3: st.markdown(f"<div class='transport-card'>🚌 <b>Bus</b><br>₹{logistics['costs']['bus']['inr']:,}<br><small>Economy (Per Person)</small></div>", unsafe_allow_html=True)
            with lc4: st.markdown(f"<div class='transport-card'>🚗 <b>Car</b><br>₹{logistics['costs']['car']['inr']:,}<br><small>{logistics['times']['car']} (Total Vehicle)</small></div>", unsafe_allow_html=True)
            st.info(f"📍 Distance: **{logistics['distance_km']:,} km**")

        # BUDGET TRACKER
        if 'selected_activities' not in st.session_state: st.session_state['selected_activities'] = {}
        curr_total = 0
        for day in data.get('days', []):
            for i, act in enumerate(day['activities']):
                key = f"{day['day']}_{i}"
                if key not in st.session_state['selected_activities']: st.session_state['selected_activities'][key] = True
                if st.session_state['selected_activities'][key]: curr_total += parse_cost(act.get('cost'))
        
        delta = max_budget - curr_total
        budget_status = "over-budget" if delta < 0 else "under-budget"
        
        # NEW: PER PERSON CALCULATION
        per_person = int(curr_total / travelers_count)
        
        c_head, c_cost = st.columns([3, 1])
        with c_cost:
             st.markdown(f"""
             <div class='cost-card {budget_status}'>
                <h3>₹{curr_total:,}</h3>
                <p>Total Spend / ₹{max_budget:,}</p>
                <div style='border-top:1px solid #444; margin-top:5px; padding-top:5px;'>
                    <b>₹{per_person:,}</b> per person
                </div>
             </div>
             """, unsafe_allow_html=True)

        # MAP
        if fo and fd:
            embed_url = f"https://maps.google.com/maps?saddr={fo.replace(' ','+')}&daddr={fd.replace(' ','+')}&output=embed"
            components.iframe(src=embed_url, height=400)

        # ITINERARY
        st.subheader("📅 Schedule")
        for day in data.get('days', []):
            with st.expander(f"Day {day['day']}", expanded=(day['day']==1)):
                for idx, act in enumerate(day['activities']):
                    c1, c2, c3 = st.columns([0.5, 3.5, 1])
                    key = f"{day['day']}_{idx}"
                    is_sel = c1.checkbox("", value=st.session_state['selected_activities'].get(key, True), key=key)
                    st.session_state['selected_activities'][key] = is_sel
                    op = "1" if is_sel else "0.5"
                    c2.markdown(f"<div style='opacity:{op}'><b>{act.get('time')}</b>: {act.get('activity')}</div>", unsafe_allow_html=True)
                    c2.caption(act.get('description'))
                    c3.markdown(f"<div style='opacity:{op}'><b>{act.get('cost')}</b></div>", unsafe_allow_html=True)

        # RECOMMENDATIONS
        st.subheader("💎 Recommendations")
        t1, t2 = st.tabs(["Hotels", "Food"])
        with t1:
            for h in data.get('hotel_recommendations', []):
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{h.get('name')}**")
                    c1.caption(f"📍 {h.get('location')}")
                    c2.markdown(f"**{h.get('price_per_night')}**")
                    search = f"{h.get('name')} {fd.split(',')[0]} hotel"
                    c2.link_button("Map", f"https://www.google.com/maps/search/?api=1&query={search.replace(' ','+')}")
        with t2:
            for f in data.get('dining_recommendations', []):
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{f.get('name')}**")
                    c1.caption(f"🥘 {f.get('type','Food')}")
                    c2.markdown(f"**{f.get('price')}**")
                    search = f"{f.get('name')} {fd.split(',')[0]} food"
                    c2.link_button("Map", f"https://www.google.com/maps/search/?api=1&query={search.replace(' ','+')}")