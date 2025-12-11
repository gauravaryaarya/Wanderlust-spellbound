# src/static_data.py

def get_smart_fallback(destination, duration, trip_type):
    """
    Generates a rich, non-repetitive itinerary when AI is offline.
    """
    days = []
    
    # Diverse Themes to prevent "Day 1 Loop"
    themes = [
        {"theme": "Arrival & Discovery", "act": "City Center Walk & Check-in", "desc": "Explore the main plaza and settle in."},
        {"theme": "History & Culture", "act": "Museums & Ancient Forts", "desc": "Deep dive into local heritage."},
        {"theme": "Nature & Parks", "act": "Botanical Gardens", "desc": "Relax amidst nature and greenery."},
        {"theme": "Local Vibe", "act": "Market & Street Food", "desc": "Taste the authentic local flavors."},
        {"theme": "Adventure", "act": "Hiking or Cycling Tour", "desc": "Get active with a city view."},
        {"theme": "Art & Soul", "act": "Galleries & Workshops", "desc": "Experience the creative side."},
        {"theme": "Shopping Spree", "act": "Grand Bazaar Visit", "desc": "Hunt for souvenirs and crafts."},
        {"theme": "Relaxation", "act": "Spa or River Cruise", "desc": "Unwind and recharge."},
        {"theme": "Hidden Gems", "act": "Off-beat Alleyways", "desc": "Discover the parts tourists miss."},
        {"theme": "Departure", "act": "Final Views & Airport", "desc": "One last coffee before you go."}
    ]

    for i in range(1, duration + 1):
        # Pick a unique theme based on the day number
        if i == 1:
            t = themes[0] # Always Arrival
        elif i == duration:
            t = themes[-1] # Always Departure
        else:
            # Cycle through middle themes
            t = themes[(i % (len(themes) - 2)) + 1]
            
        days.append({
            "day": i,
            "daily_total": f"₹{3000 + (i*200)}",
            "activities": [
                {"time": "09:00", "activity": f"{t['theme']}: Morning", "description": t['desc'], "location": destination, "cost": "₹500"},
                {"time": "14:00", "activity": f"{t['theme']}: Afternoon", "description": "Local exploration and sightseeing.", "location": destination, "cost": "₹1,500"},
                {"time": "20:00", "activity": "Evening Leisure", "description": "Dinner at a recommended local spot.", "location": destination, "cost": "₹1,000"}
            ]
        })

    # Rich Recommendations (Always Full)
    hotels = [
        {"name": "Grand City Stay", "location": "Downtown", "price_per_night": "₹5,000 ($60)", "rating": "4.8"},
        {"name": "The Backpackers Loft", "location": "Old Town", "price_per_night": "₹1,200 ($15)", "rating": "4.3"},
        {"name": "Riverside Boutique", "location": "River Bank", "price_per_night": "₹8,000 ($95)", "rating": "4.7"},
        {"name": "City Center Inn", "location": "Main Plaza", "price_per_night": "₹3,500 ($42)", "rating": "4.0"},
        {"name": "Heritage Haveli", "location": "Historic District", "price_per_night": "₹6,000 ($72)", "rating": "4.6"}
    ]
    
    food = [
        {"name": "The Golden Spoon", "type": "Fine Dining", "location": "City Center", "price": "₹2,500 ($30)"},
        {"name": "Street Flavors", "type": "Snacks", "location": "Market", "price": "₹200 ($3)"},
        {"name": "Cafe Sol", "type": "Coffee & Brunch", "location": "Art District", "price": "₹600 ($7)"},
        {"name": "Mama's Kitchen", "type": "Traditional", "location": "Old Town", "price": "₹1,200 ($15)"},
        {"name": "Spice Route", "type": "Curry House", "location": "Main St", "price": "₹900 ($11)"}
    ]

    return {
        "trip_title": f"The Ultimate {destination} Experience",
        "travel_persona": f"The {trip_type} Explorer",
        "total_estimated_cost": f"₹{duration * 5000}",
        "days": days,
        "hotel_recommendations": hotels,
        "dining_recommendations": food,
        "safety_tips": "Keep emergency numbers saved and stay hydrated."
    }