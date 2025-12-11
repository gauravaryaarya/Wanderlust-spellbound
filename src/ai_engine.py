import google.generativeai as genai
import json
import os
import time
import re
import logging
import streamlit as st
from groq import Groq 

# --- CONFIG ---
GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash"]
GROQ_MODEL = "llama3-70b-8192" 

logging.basicConfig(level=logging.INFO)

def get_api_key(name):
    return st.secrets.get(name) or os.getenv(name)

def configure_genai():
    key = get_api_key("GOOGLE_API_KEY")
    if key: genai.configure(api_key=key)

def extract_json(text):
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE).replace("```", "")
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except: pass
    try: return json.loads(text)
    except: return None

# --- ENGINE 3: SMART SIMULATION ---
def generate_smart_fallback(destination, duration, budget):
    days = []
    themes = [
        ("Arrival & Check-in", "Explore the city center.", "₹500 ($6)"),
        ("Historical Landmarks", "Visit the main museum.", "₹1,500 ($18)"),
        ("Culture Dive", "Art gallery and cultural show.", "₹2,000 ($24)"),
        ("Nature Escape", "Botanical gardens visit.", "₹800 ($10)"),
        ("Shopping Spree", "Visit the Grand Bazaar.", "₹3,000 ($35)"),
        ("Relaxation", "Spa or leisure walk.", "₹1,200 ($15)"),
        ("Adventure", "Hiking or cycling tour.", "₹2,500 ($30)"),
        ("Food Tour", "Street food tasting.", "₹1,000 ($12)"),
        ("Hidden Gems", "Off-beat alleys.", "₹500 ($6)"),
        ("Departure", "Souvenirs and airport.", "₹1,000 ($12)")
    ]

    for i in range(1, duration + 1):
        idx = (i - 1) % len(themes)
        title, desc, cost = themes[idx]
        
        days.append({
            "day": i,
            "activities": [
                {"time": "09:00", "activity": f"{title}: Morning", "description": desc, "location": destination, "cost": "₹500 ($6)"},
                {"time": "14:00", "activity": f"{title}: Afternoon", "description": "Local exploration.", "location": destination, "cost": cost},
                {"time": "20:00", "activity": "Evening Leisure", "description": "Dinner at a local spot.", "location": destination, "cost": "₹1,500 ($18)"}
            ]
        })

    return {
        "trip_title": f"The Ultimate {destination} Experience",
        "travel_persona": "The Smart Traveler (Offline Mode)",
        "days": days,
        "hotel_recommendations": [
            {"name": "Grand City Stay", "location": "Downtown", "price_per_night": "₹5,000 ($60)"},
            {"name": "The Backpackers Loft", "location": "Old Town", "price_per_night": "₹1,200 ($15)"},
            {"name": "Riverside Boutique", "location": "River Bank", "price_per_night": "₹8,000 ($95)"},
            {"name": "City Center Inn", "location": "Main Plaza", "price_per_night": "₹3,500 ($42)"}
        ],
        "dining_recommendations": [
            {"name": "The Golden Spoon", "type": "Fine Dining", "location": "City Center", "price": "₹2,500 ($30)"},
            {"name": "Street Flavors", "type": "Snacks", "location": "Market", "price": "₹200 ($3)"},
            {"name": "Cafe Sol", "type": "Cafe", "location": "Art District", "price": "₹600 ($7)"},
            {"name": "Mama's Kitchen", "type": "Traditional", "location": "Old Town", "price": "₹1,200 ($15)"}
        ],
        "safety_tips": "Keep emergency numbers saved."
    }

# --- ENGINE 1 & 2: GOOGLE & GROQ ---
@st.cache_data(ttl=3600, show_spinner=False)
def generate_itinerary(destination, start_date, duration, budget, max_budget, travelers, trip_type, interests):
    # UPDATED PROMPT WITH GROUP SIZE CONTEXT
    prompt = f"""
    ROLE: Expert Travel Planner. TASK: {duration}-Day Trip to {destination}.
    GROUP: {travelers} people ({trip_type}).
    BUDGET: {budget} (Cap: ₹{max_budget}). Interests: {', '.join(interests)}.
    
    RULES:
    1. REALISTIC PRICES: ₹Amount ($USD).
    2. COSTS MUST BE TOTAL FOR THE GROUP (e.g., if 4 people, show total for 4 tickets).
    3. FULL SCHEDULE: Day 1 to Day {duration}.
    4. STRICT JSON FORMAT.
    
    OUTPUT JSON:
    {{
        "trip_title": "Title",
        "travel_persona": "Persona",
        "days": [
            {{
                "day": 1, 
                "activities": [
                    {{"time": "09:00", "activity": "Name", "description": "Desc", "location": "Area", "cost": "₹XXX ($YY)"}}
                ]
            }}
        ],
        "hotel_recommendations": [
            {{"name": "Name", "location": "Area", "price_per_night": "₹XXX ($YY)"}}
        ],
        "dining_recommendations": [
             {{"name": "Name", "type": "Cuisine", "location": "Area", "price": "₹XXX ($YY)"}}
        ],
        "safety_tips": "Tip"
    }}
    """
    
    # 1. Try Gemini
    for model in GEMINI_MODELS:
        try:
            m = genai.GenerativeModel(model)
            res = m.generate_content(prompt)
            data = extract_json(res.text)
            if data and "days" in data and len(data["days"]) >= 1: return data
        except: continue

    # 2. Try Groq
    groq_key = get_api_key("GROQ_API_KEY")
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL
            )
            data = extract_json(resp.choices[0].message.content)
            if data and "days" in data: return data
        except: pass

    # 3. Last Resort
    return generate_smart_fallback(destination, duration, budget)

def ask_travel_bot(history, question):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=history)
        return chat.send_message(question).text
    except:
        return "I am currently offline. Please check the itinerary details!"