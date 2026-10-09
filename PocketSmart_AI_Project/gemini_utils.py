import os, json, re
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

def money(value):
    try:
        return f"₹{float(value):,.0f}"
    except Exception:
        return str(value)

def search_link(site, query):
    q = quote_plus(query)
    sites = {
        "Amazon": f"https://www.amazon.in/s?k={q}",
        "Flipkart": f"https://www.flipkart.com/search?q={q}",
        "IKEA": f"https://www.ikea.com/in/en/search/?q={q}",
        "Swiggy": f"https://www.swiggy.com/search?query={q}",
        "Zomato": f"https://www.zomato.com/search?query={q}",
        "OYO": f"https://www.oyorooms.com/search?q={q}"
    }
    return sites.get(site, "#")

def try_gemini(prompt, image_bytes=None, image_mime=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    # Uses the current google-genai SDK. The model name can be changed in .env.
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        contents = [prompt]
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime or "image/jpeg"))
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.5,
                response_mime_type="application/json"
            )
        )
        text = response.text
        return json.loads(text)
    except Exception:
        return None

def fallback_home(data):
    budget = float(data.get("budget", 0))
    room = data.get("room_type", "Living Room")
    style = data.get("style", "Modern")
    items = data.get("items", "lights, fan, table")
    base = max(budget / 3, 500)
    return {
        "title": "Budget Home Plan",
        "summary": f"A {style} {room} setup planned around {money(budget)}.",
        "budget": budget,
        "allocation": [
            {"category": "Lighting", "amount": round(budget*0.18), "reason": "Good lighting improves comfort and appearance."},
            {"category": "Furniture", "amount": round(budget*0.47), "reason": "Largest share for essential furniture."},
            {"category": "Decor", "amount": round(budget*0.20), "reason": "Keeps styling within budget."},
            {"category": "Buffer", "amount": round(budget*0.15), "reason": "Reserved for delivery or unexpected cost."}
        ],
        "recommendations": [
            {"name": f"{style} LED lighting", "price": round(base), "platform": "Amazon", "reason": f"Suitable for {room}.", "link": search_link("Amazon", f"{room} {style} LED light")},
            {"name": f"{style} table", "price": round(base*2.2), "platform": "IKEA", "reason": "Functional and simple design.", "link": search_link("IKEA", f"{room} {style} table")},
            {"name": "Ceiling fan", "price": round(base*1.8), "platform": "Flipkart", "reason": "Practical utility item.", "link": search_link("Flipkart", "ceiling fan")}
        ]
    }

def fallback_party(data):
    budget = float(data.get("budget", 0))
    guests = int(data.get("guests", 1))
    event = data.get("event_type", "Birthday")
    return {
        "title": "Budget Party Plan",
        "summary": f"{event} plan for {guests} guests within {money(budget)}.",
        "budget": budget,
        "allocation": [
            {"category": "Food", "amount": round(budget*0.50), "reason": "Food is usually the main event expense."},
            {"category": "Decoration", "amount": round(budget*0.20), "reason": "Creates the event atmosphere."},
            {"category": "Entertainment", "amount": round(budget*0.15), "reason": "Keeps the event engaging."},
            {"category": "Buffer", "amount": round(budget*0.15), "reason": "Allows flexibility."}
        ],
        "recommendations": [
            {"name": f"Catering for {guests} guests", "price": round(budget*0.50), "platform": "Swiggy", "reason": "Food package estimate.", "link": search_link("Swiggy", f"{event} catering {guests} people")},
            {"name": "Party decorations", "price": round(budget*0.20), "platform": "Amazon", "reason": "Basic decoration bundle.", "link": search_link("Amazon", f"{event} party decorations")},
            {"name": "Event venue options", "price": round(budget*0.15), "platform": "OYO", "reason": "Search nearby stay/event options.", "link": search_link("OYO", f"{event} venue")}
        ]
    }

def fallback_jewelry(data):
    budget = float(data.get("budget", 0))
    occasion = data.get("occasion", "Special Occasion")
    style = data.get("style", "Traditional")
    color = data.get("color", "Any")
    return {
        "title": "Budget Jewelry Plan",
        "summary": f"{style} jewelry suggestions for {occasion}, coordinated with {color or 'your outfit'} within {money(budget)}.",
        "budget": budget,
        "recommendations": [
            {"name": f"{style} necklace set", "price": round(budget*0.45), "platform": "Amazon", "reason": "A versatile centerpiece.", "link": search_link("Amazon", f"{style} necklace {color}")},
            {"name": f"{style} earrings", "price": round(budget*0.25), "platform": "Flipkart", "reason": "Complements the main jewelry.", "link": search_link("Flipkart", f"{style} earrings {color}")},
            {"name": "Bangle set", "price": round(budget*0.15), "platform": "Amazon", "reason": "Adds coordinated detail.", "link": search_link("Amazon", f"{style} bangles {color}")}
        ],
        "image_analysis": "Image was received and considered as optional outfit context." if data.get("image_uploaded") else "No outfit image uploaded."
    }

def generate_home(data):
    prompt = f"""You are PocketSmart AI. Create practical budget-aware home interior recommendations.
Return ONLY valid JSON with keys: title, summary, budget, allocation (array of category/amount/reason),
recommendations (array of name/price/platform/reason/link).
Budget: {data.get('budget')}; room: {data.get('room_type')}; style: {data.get('style')};
items: {data.get('items')}. Use Amazon, Flipkart or IKEA as platform names.
Links may be search links rather than claims of live product availability."""
    return try_gemini(prompt) or fallback_home(data)

def generate_party(data):
    prompt = f"""You are PocketSmart AI. Create a realistic party budget plan.
Return ONLY valid JSON with keys: title, summary, budget, allocation, recommendations.
Each recommendation must have name, price, platform, reason, link.
Budget: {data.get('budget')}; guests: {data.get('guests')}; event: {data.get('event_type')};
venue: {data.get('venue')}. Use Swiggy, Zomato, OYO or Amazon as platform names."""
    return try_gemini(prompt) or fallback_party(data)

def generate_jewelry(data, image_bytes=None, image_mime=None):
    prompt = f"""You are PocketSmart AI. Recommend jewelry for an occasion and budget.
Return ONLY valid JSON with keys: title, summary, budget, recommendations, image_analysis.
Each recommendation must have name, price, platform, reason, link.
Budget: {data.get('budget')}; occasion: {data.get('occasion')}; style: {data.get('style')};
outfit color: {data.get('color')}; image uploaded: {data.get('image_uploaded')}.
Use Amazon or Flipkart as platform names. Do not identify a person in the image."""
    return try_gemini(prompt, image_bytes, image_mime) or fallback_jewelry(data)
