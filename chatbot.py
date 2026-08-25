import os
from pathlib import Path
import requests


# ----------------------------------------------------------
# NER-SMARTLOG KNOWLEDGE BASE
# ----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_FILE = BASE_DIR / "data" / "northeast_knowledge.txt"


def load_knowledge():
    """Load the NER-SMARTLOG knowledge base."""
    try:
        return KNOWLEDGE_FILE.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Knowledge base error: {e}")
        return ""


# ----------------------------------------------------------
# GEMINI CHATBOT
# ----------------------------------------------------------

def ask_gemini(user_message, incidents=None, vehicles=None):
    """
    Send the user's question to Gemini together with:
    - NER-SMARTLOG knowledge
    - Current incidents
    - Current convoy/vehicle information
    """

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not gemini_key:
        return None

    incidents = incidents or []
    vehicles = vehicles or []

    knowledge = load_knowledge()

    # Current incident information
    active_incidents = []

    for inc in incidents:
        active_incidents.append(
            f"{inc.get('type', 'Unknown incident')} at "
            f"{inc.get('location', 'Unknown location')} "
            f"(Severity: {inc.get('severity', 'Unknown')})"
        )

    active_incidents_text = (
        "; ".join(active_incidents)
        if active_incidents
        else "No active incidents recorded."
    )

    # Current convoy information
    active_vehicles = []

    for vehicle in vehicles:
        active_vehicles.append(
            f"{vehicle.get('id', 'Unknown vehicle')} "
            f"carrying {vehicle.get('cargo', 'Unknown cargo')} "
            f"from {vehicle.get('origin', 'Unknown origin')} "
            f"to {vehicle.get('destination', 'Unknown destination')}, "
            f"status: {vehicle.get('status', 'Unknown')}, "
            f"speed: {vehicle.get('speed', 'Unknown')}"
        )

    active_vehicles_text = (
        "; ".join(active_vehicles)
        if active_vehicles
        else "No active convoy information available."
    )

    system_prompt = f"""
You are NER-SMARTBOT, the AI logistics and hazard intelligence
assistant for the NER-SMARTLOG portal.

NER-SMARTLOG focuses on logistics, transportation, weather awareness,
route planning and disaster awareness in Northeast India.

The eight states covered are:

1. Assam
2. Arunachal Pradesh
3. Meghalaya
4. Manipur
5. Mizoram
6. Nagaland
7. Tripura
8. Sikkim

PROJECT KNOWLEDGE:
{knowledge}

CURRENT PORTAL INCIDENT DATA:
{active_incidents_text}

CURRENT PORTAL VEHICLE/CONVOY DATA:
{active_vehicles_text}

RULES:

1. Answer questions related to Northeast India, logistics, routes,
   weather awareness, vehicles, convoys and hazards.

2. Use the supplied project knowledge when answering questions.

3. Use the supplied current incident and vehicle information when
   relevant.

4. Do NOT invent live weather information.

5. Do NOT claim that a road is currently open, closed, blocked or safe
   unless the supplied live data confirms it.

6. If the user asks for current weather, explain that live weather
   should come from the application's weather data/API.

7. Clearly distinguish between project knowledge and live information.

8. If you don't know something, say so instead of inventing an answer.

9. If the question is completely unrelated to NER-SMARTLOG or Northeast
   India, politely explain that you are specialized in Northeast
   logistics and hazard intelligence.

10. Keep answers concise and useful.

11. Use bullet points when appropriate.

12. You may use these emojis when useful:
    🚚 🛣️ 🌦️ ⛰️ ⚠️ 🚨 🛡️

USER QUESTION:
{user_message}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-1.5-flash:generateContent"
        f"?key={gemini_key}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": system_prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            print(
                f"Gemini API error: "
                f"{response.status_code} - {response.text}"
            )
            return None

        result = response.json()

        candidates = result.get("candidates", [])

        if not candidates:
            return None

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        if not parts:
            return None

        return parts[0].get("text")

    except Exception as e:
        print(f"Gemini request failed: {e}")
        return None
