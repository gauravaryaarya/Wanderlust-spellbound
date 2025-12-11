import google.generativeai as genai
import json
import os
import streamlit as st

# Configure API
def configure_genai():
    # We will use Streamlit Secrets for deployment safety
    api_key = st.secrets["GOOGLE_API_KEY"] 
    genai.configure(api_key=api_key)

def generate_itinerary(destination, start_date, duration, budget, travelers, interests):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Act as an expert travel planner agent. Create a detailed {duration}-day trip to {destination} for a {travelers} trip.
    Budget: {budget}. Interests: {', '.join(interests)}.
    Start Date: {start_date}.

    Requirements:
    1. Provide a day-by-day itinerary with timings (Morning, Afternoon, Evening).
    2. Suggest specific hotels and restaurants fitting the {budget} budget.
    3. Include estimated costs for activities.
    4. Mention safety tips and local customs.
    5. FORMAT THE RESPONSE AS STRICT JSON with this structure:
    {{
        "trip_title": "Trip Name",
        "summary": "Brief summary",
        "days": [
            {{
                "day": 1,
                "date": "YYYY-MM-DD",
                "activities": [
                    {{"time": "09:00 AM", "activity": "Activity Name", "description": "Details", "location": "Lat,Lon (approx)", "cost": "$XX"}}
                ]
            }}
        ],
        "hotel_recommendations": ["Hotel A", "Hotel B"],
        "dining_recommendations": ["Rest A", "Rest B"],
        "packing_list": ["Item 1", "Item 2"],
        "safety_tips": "Tips here"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up json string if the model adds markdown
        text = response.text.replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

def ask_travel_bot(history, question):
    # Chatbot feature for "Agent-OS" feel
    model = genai.GenerativeModel('gemini-1.5-flash')
    chat = model.start_chat(history=history)
    response = chat.send_message(question)
    return response.text