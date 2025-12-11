import google.generativeai as genai
import json
import os
import time
import re
import logging
import streamlit as st
from groq import Groq  # <--- NEW: Backup Brain

# --- CONFIG ---
# We try Google first. If it fails, we switch to Llama 3 via Groq.
GEMINI_MODELS = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-8b"]
GROQ_MODEL = "llama3-70b-8192" 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
def get_api_key(name):
    return st.secrets.get(name) or os.getenv(name)

def configure_genai():
    # Only needed for Gemini
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

# --- ENGINE 1: GOOGLE GEMINI ---
def call_gemini(model_name, prompt):
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except:
        return None

# --- ENGINE 2: GROQ (LLAMA 3) ---
def call_groq(prompt):
    key = get_api_key("GROQ_API_KEY")
    if not key: return None # Skip if no key provided
    
    try:
        client = Groq(api_key=key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only API. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.5,
        )
        return extract_json(chat_completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return None

# --- ENGINE 3: SMART SIMULATION (The "Never Fail" Safety Net) ---
def generate_smart_fallback(destination, duration):
    """
    Mathematically generates a valid schedule if ALL AI fails.
    """
    days = []
    themes = [
        ("Arrival & Discovery", "Explore city center.", "₹500 ($6)"),
        ("Culture Dive", "Museums and history.", "₹1,500 ($18)"),
        ("Nature Escape", "Parks and gardens.", "₹800 ($10)"),
        ("Local Vibe", "Markets and street food.", "₹1,000 ($12)"),
        ("Leisure", "Relaxation and cafes.", "₹1,200 ($15)")
    ]
    
    for i in range(1, duration + 1):
        t = themes[(i-1) % len(themes)]
        days.append({
            "day": i,
            "activities": [
                {"time": "09:00", "activity": f"{t[0]} (Morning)", "description": t[1], "location": destination, "cost": t[2]},
                {"time": "14:00", "activity": f"{t[0]} (Afternoon)", "description": "Continue exploring.", "location": destination, "cost": t[2]},
                {"time": "19:00", "activity": "Dinner", "description": "Local cuisine.", "location": destination, "cost": "₹800 ($10)"}
            ]
        })

    return {
        "trip_title": f"Trip to {destination}",
        "travel_persona": "The Unstoppable Traveler",
        "days": days,
        "hotel_recommendations": [{"name": "City Central Hotel", "location": "Center", "price_per_night": "₹4,000 ($48)"}],
        "dining_recommendations": [{"name": "Local Bistro", "type": "Local", "location": "Center", "price": "₹800 ($10)"}],
        "safety_tips": "Standard safety precautions apply."
    }

@st.cache_data(ttl=3600, show_spinner=False)
def generate_itinerary(destination, start_date, duration, budget, max_budget, travelers, interests):
    prompt = f"""
    ROLE: Expert Travel Planner. TASK: {duration}-Day Trip to {destination}.
    BUDGET: {budget} (Cap: ₹{max_budget}). Interests: {', '.join(interests)}.
    
    RULES:
    1. REALISTIC PRICES: ₹Amount ($USD).
    2. FULL SCHEDULE: Day 1 to Day {duration}.
    3. STRICT JSON FORMAT.
    
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
    
    # 1. Try Gemini Models
    for model in GEMINI_MODELS:
        data = call_gemini(model, prompt)
        if data and "days" in data and len(data["days"]) >= 1:
            return data
            
    # 2. Try Groq (Llama 3)
    data = call_groq(prompt)
    if data and "days" in data:
        return data

    # 3. Last Resort: Simulation
    return generate_smart_fallback(destination, duration)

def ask_travel_bot(history, question):
    # Try Gemini Chat
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=history)
        return chat.send_message(question).text
    except:
        # Try Groq Chat
        key = get_api_key("GROQ_API_KEY")
        if key:
            try:
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    messages=[{"role": "user", "content": question}],
                    model=GROQ_MODEL
                )
                return resp.choices[0].message.content
            except: pass
            
    return "I am currently offline. Please check the itinerary details!"