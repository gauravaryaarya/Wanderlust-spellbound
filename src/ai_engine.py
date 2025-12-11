import google.generativeai as genai
import json
import os
import re
import logging
import streamlit as st
from groq import Groq
from src.static_data import get_smart_fallback # <--- Import the safety net

GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash"]
GROQ_MODEL = "llama3-70b-8192" 
logging.basicConfig(level=logging.INFO)

def get_key(name): return st.secrets.get(name) or os.getenv(name)

def configure_genai():
    k = get_key("GOOGLE_API_KEY")
    if k: genai.configure(api_key=k)

def extract_json(text):
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE).replace("```", "")
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except: pass
    try: return json.loads(text)
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def generate_itinerary(destination, start_date, duration, budget, max_budget, travelers, trip_type, interests):
    prompt = f"""
    ROLE: Expert Travel Planner. TASK: {duration}-Day Trip to {destination} for {travelers} ({trip_type}).
    BUDGET: {budget} (Cap: ₹{max_budget}). Interests: {', '.join(interests)}.
    
    RULES:
    1. PRICES: ₹Amount.
    2. TOTAL GROUP COST: If 4 people, show total for 4.
    3. FULL SCHEDULE: Day 1 to Day {duration} (NO REPEATING DAYS).
    4. STRICT JSON.
    
    OUTPUT JSON:
    {{
        "trip_title": "Title",
        "travel_persona": "Persona",
        "total_estimated_cost": "₹XXXX",
        "days": [
            {{
                "day": 1, 
                "activities": [
                    {{"time": "09:00", "activity": "Name", "description": "Desc", "location": "Area", "cost": "₹XXX"}}
                ]
            }}
        ],
        "hotel_recommendations": [
            {{"name": "Name", "location": "Area", "rating": "4.5", "price_per_night": "₹XXX"}}
        ],
        "dining_recommendations": [
             {{"name": "Name", "type": "Cuisine", "location": "Area", "price": "₹XXX"}}
        ],
        "safety_tips": "Tip"
    }}
    """
    
    # 1. Gemini
    for m in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(m)
            res = model.generate_content(prompt)
            data = extract_json(res.text)
            if data and len(data.get("days", [])) >= 1: return data
        except: continue

    # 2. Groq
    gk = get_key("GROQ_API_KEY")
    if gk:
        try:
            client = Groq(api_key=gk)
            resp = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=GROQ_MODEL)
            data = extract_json(resp.choices[0].message.content)
            if data and len(data.get("days", [])) >= 1: return data
        except: pass

    # 3. STATIC FALLBACK (Guaranteed to work)
    return get_smart_fallback(destination, duration, trip_type)

def ask_travel_bot(history, question):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=history)
        return chat.send_message(question).text
    except:
        return "I'm offline right now, but you can check the itinerary tabs for details!"