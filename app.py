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
        font-size: 60px; font-weight: bold; text-align: center;
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
    .auto-tag {
        font-size:12px; background:#333; padding:2px 8px; border-radius:10px; color:#aaa; margin-left:10px;
    }
</style>
""", unsafe_allow_html=True)

def parse_cost(cost_str):
    if not cost_str: return 0
    match = re.search(r"₹([\d,]+)", str(cost_str))
    if match: return int(match.group(1).replace(",", ""))
    return 0

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
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="title-animate">WANDERLUST AI</p>', unsafe_allow_html=True)
        st.markdown("<center>Your AI-Powered Travel Architect</center>", unsafe_allow_html=True)
    time.sleep(2)
    empty.empty()
    st.session_state['page'] = 'login'
    st.rerun()

# --- LOGIN ---
elif st.session_state['page'] == 'login':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("✈️ Start Journey")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", type="primary"):
                if check_login(u, p):
                    st.session_state['user'] = u
                    st.session_state['page'] = 'home'
                    st.query_params["user"] = u
                    st.rerun()
                else: st.error("Invalid credentials")
        with tab2:
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                if add_user(nu, np): st.success("Created! Login now.")
                else: st.error("Username taken.")

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
                if st.button("View Plan", key=f"l_{tid}"):
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
        sd = c3.date_input("Start Date")
        dur = c4.slider("Duration (Days)", 1, 10, 3)
        
        # --- AUTO-BUDGET LOGIC ---
        # No more slider. We calculate style from the Max Budget amount.
        max_budget = c5.number_input("Total Trip Budget (₹)", 5000, 2000000, 20000, 1000)
        
        if max_budget < 30000:
            bud_type = "Cheap"
            bud_icon = "🎒 Backpacker Style"
        elif max_budget < 100000:
            bud_type = "Mid"
            bud_icon = "⚖️ Standard Comfort"
        else:
            bud_type = "Lux"
            bud_icon = "💎 Luxury Experience"
            
        # Show the detected style to the user
        c5.markdown(f"**Detected Style:** {bud_icon}")

        c6, c7 = st.columns(2)
        travelers = c6.number_input("Travelers", 1, 10, 1)
        trip_type = c7.selectbox("Trip Type", ["Solo", "Couple", "Family", "Friends"])
        
        intr = st.multiselect("Interests", ["Food", "Nature", "History", "Adventure", "Nightlife", "Shopping", "Relaxation"], ["Food"])
        
        if st.button("🚀 Generate Itinerary", type="primary"):
            if fd and fo:
                with st.spinner("Analyzing routes, costs, and places..."):
                    configure_genai()
                    st.session_state['selected_activities'] = {}
                    
                    # 1. AI (or Static Fallback) - Passing the AUTO DETECTED 'bud_type'
                    trip_data = generate_itinerary(fd, sd, dur, bud_type, max_budget, travelers, trip_type, intr)
                    
                    # 2. Logistics (Math)
                    logistics = get_trip_logistics(fo, fd)
                    
                    if "error" not in trip_data:
                        save_trip(st.session_state['user'], fd, trip_data)
                        st.session_state['trip_data'] = trip_data
                        st.session_state['logistics'] = logistics
                        st.session_state['travelers'] = travelers
                        st.rerun()
                    else: st.error("System Busy. Try again.")

    # --- RESULTS ---
    if 'trip_data' in st.session_state:
        data = st.session_state['trip_data']
        logistics = st.session_state.get('logistics')
        travelers_count = st.session_state.get('travelers', 1)
        
        st.divider()
        st.header(data.get('trip_title', f"Trip to {fd}"))
        
        # LOGISTICS
        if logistics:
            st.subheader("✈️ Travel Options (Estimated)")
            lc1, lc2, lc3, lc4 = st.columns(4)
            with lc1: st.markdown(f"<div class='transport-card'>✈️ <b>Flight</b><br>₹{logistics['costs']['flight']['inr']:,}<br><small>{logistics['times']['flight']}</small></div>", unsafe_allow_html=True)
            with lc2: st.markdown(f"<div class='transport-card'>🚆 <b>Train</b><br>₹{logistics['costs']['train']['inr']:,}<br><small>{logistics['times']['train']}</small></div>", unsafe_allow_html=True)
            with lc3: st.markdown(f"<div class='transport-card'>🚌 <b>Bus</b><br>₹{logistics['costs']['bus']['inr']:,}<br><small>Economy</small></div>", unsafe_allow_html=True)
            with lc4: st.markdown(f"<div class='transport-card'>🚗 <b>Car</b><br>₹{logistics['costs']['car']['inr']:,}<br><small>{logistics['times']['car']}</small></div>", unsafe_allow_html=True)
            st.caption(f"📍 Distance: {logistics['distance_km']:,} km")

        # BUDGET
        if 'selected_activities' not in st.session_state: st.session_state['selected_activities'] = {}
        curr_total = 0
        for day in data.get('days', []):
            for i, act in enumerate(day['activities']):
                key = f"{day['day']}_{i}"
                if key not in st.session_state['selected_activities']: st.session_state['selected_activities'][key] = True
                if st.session_state['selected_activities'][key]: curr_total += parse_cost(act.get('cost'))
        
        # Ensure we don't divide by zero if max_budget is missing somehow
        safe_budget = max_budget if 'max_budget' in locals() else 50000
        
        delta = safe_budget - curr_total
        status = "over-budget" if delta < 0 else "under-budget"
        per_person = int(curr_total / travelers_count)
        
        c_head, c_cost = st.columns([3, 1])
        with c_cost:
             st.markdown(f"""
             <div class='cost-card {status}'>
                <h3>₹{curr_total:,}</h3>
                <p>Total / ₹{safe_budget:,}</p>
                <hr style='border-color:#444;'>
                <b>₹{per_person:,}</b> / person
             </div>
             """, unsafe_allow_html=True)

        # MAP (Unblockable Embed)
        if fo and fd:
            embed_url = f"https://maps.google.com/maps?saddr={fo.replace(' ','+')}&daddr={fd.replace(' ','+')}&output=embed"
            components.iframe(src=embed_url, height=400)

        # ITINERARY
        st.subheader("📅 Your Schedule")
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
        st.subheader("💎 Smart Recommendations")
        t1, t2, t3 = st.tabs(["Hotels", "Food", "AI Chat"])
        with t1:
            for h in data.get('hotel_recommendations', []):
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{h.get('name')}**")
                    c1.caption(f"📍 {h.get('location')} | ⭐ {h.get('rating', '4.5')}")
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
        with t3:
            st.write("Ask questions about this trip:")
            q = st.text_input("Example: Is it safe at night?")
            if q: st.info(ask_travel_bot([], f"Context: {str(data)}. Q: {q}"))