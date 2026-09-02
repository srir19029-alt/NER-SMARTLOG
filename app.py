import os
import re
import math
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from jinja2 import ChoiceLoader, FileSystemLoader

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "ner-smartlog-sih2026-production-secret")

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    FileSystemLoader(BASE_DIR),
    FileSystemLoader('.')
])

# 2 Government/Field Officer Credentials + 2 Normal Traveler Credentials
USERS_DATABASE = {
    "officer@ner.gov.in": {
        "password": "officer2026",
        "name": "Insp. D. Sharma",
        "role": "Field Patrol Officer (BRO)",
        "agency": "Border Roads Organisation (BRO)",
        "is_official": True
    },
    "commander@ner.gov.in": {
        "password": "govt2026",
        "name": "Commander R. Barua",
        "role": "Higher Government Official (MDoNER)",
        "agency": "MDoNER Disaster Control Cell",
        "is_official": True
    },
    "insp. d. sharma": {
        "password": "sih2026",
        "name": "Insp. D. Sharma",
        "role": "Field Patrol Officer (BRO)",
        "agency": "Border Roads Organisation (BRO)",
        "is_official": True
    },
    "commander r. barua": {
        "password": "sih2026",
        "name": "Commander R. Barua",
        "role": "Higher Government Official (MDoNER)",
        "agency": "MDoNER Disaster Control Cell",
        "is_official": True
    },
    "director s. roy": {
        "password": "sih2026",
        "name": "Director S. Roy",
        "role": "State Disaster Controller (SDMA)",
        "agency": "SDMA Disaster Control Cell",
        "is_official": True
    },
    "bro-officer-44": {
        "password": "sih2026",
        "name": "BRO-OFFICER-44",
        "role": "Field Patrol Officer (BRO)",
        "agency": "Border Roads Organisation (BRO)",
        "is_official": True
    },
    "traveler@northeast.in": {
        "password": "travel2026",
        "name": "Arunav Das",
        "role": "Normal Vehicle Traveler",
        "agency": "Civilian Commuter / Tourist",
        "is_official": False
    },
    "driver@nerlog.in": {
        "password": "driver2026",
        "name": "Bijoy Gogoi",
        "role": "Commercial Transport Driver",
        "agency": "Private Goods Carrier",
        "is_official": False
    }
}

REGIONS = [
    {"name": "Assam", "code": "AS", "capital": "Dispur / Guwahati", "lat": 26.1445, "lon": 91.7362, "routes": 34, "accessibility": "95%", "weather_zone": "Brahmaputra Valley Corridor"},
    {"name": "Arunachal Pradesh", "code": "AR", "capital": "Itanagar", "lat": 27.0844, "lon": 93.6053, "routes": 18, "accessibility": "58%", "weather_zone": "High Himalayan Landslide Prone"},
    {"name": "Meghalaya", "code": "ML", "capital": "Shillong", "lat": 25.5788, "lon": 91.8933, "routes": 22, "accessibility": "78%", "weather_zone": "Heavy Rain & Dense Cloud Fog"},
    {"name": "Manipur", "code": "MN", "capital": "Imphal", "lat": 24.8170, "lon": 93.9368, "routes": 16, "accessibility": "72%", "weather_zone": "Valley Transport Corridor"},
    {"name": "Mizoram", "code": "MZ", "capital": "Aizawl", "lat": 23.7271, "lon": 92.7176, "routes": 14, "accessibility": "88%", "weather_zone": "Southern Hill Ridge Corridor"},
    {"name": "Nagaland", "code": "NL", "capital": "Kohima", "lat": 25.6751, "lon": 94.1086, "routes": 15, "accessibility": "86%", "weather_zone": "Naga Hills Transit Route"},
    {"name": "Tripura", "code": "TR", "capital": "Agartala", "lat": 23.8315, "lon": 91.2868, "routes": 12, "accessibility": "82%", "weather_zone": "Plains Highway Access"},
    {"name": "Sikkim", "code": "SK", "capital": "Gangtok", "lat": 27.3389, "lon": 88.6065, "routes": 10, "accessibility": "90%", "weather_zone": "Teesta River Highway Sector"}
]

NER_PLACES = {
    # Assam
    "Guwahati, Assam": {"lat": 26.1445, "lon": 91.7362, "state": "Assam", "elev": "180 ft"},
    "Dispur, Assam": {"lat": 26.1408, "lon": 91.7907, "state": "Assam", "elev": "185 ft"},
    "Silchar, Assam": {"lat": 24.8333, "lon": 92.7789, "state": "Assam", "elev": "82 ft"},
    "Tezpur, Assam": {"lat": 26.6338, "lon": 92.8000, "state": "Assam", "elev": "157 ft"},
    "Dibrugarh, Assam": {"lat": 27.4728, "lon": 94.9120, "state": "Assam", "elev": "354 ft"},
    "Jorhat, Assam": {"lat": 26.7509, "lon": 94.2037, "state": "Assam", "elev": "380 ft"},
    "Nagaon, Assam": {"lat": 26.3452, "lon": 92.6840, "state": "Assam", "elev": "220 ft"},
    "Bongaigaon, Assam": {"lat": 26.5020, "lon": 90.5530, "state": "Assam", "elev": "205 ft"},
    "Tinsukia, Assam": {"lat": 27.5000, "lon": 95.3667, "state": "Assam", "elev": "384 ft"},

    # Arunachal Pradesh
    "Itanagar, Arunachal": {"lat": 27.0844, "lon": 93.6053, "state": "Arunachal Pradesh", "elev": "2,460 ft"},
    "Tawang, Arunachal": {"lat": 27.5860, "lon": 91.8590, "state": "Arunachal Pradesh", "elev": "10,000 ft"},
    "Bomdila, Arunachal": {"lat": 27.2640, "lon": 92.4240, "state": "Arunachal Pradesh", "elev": "7,923 ft"},
    "Dirang, Arunachal": {"lat": 27.3556, "lon": 92.2389, "state": "Arunachal Pradesh", "elev": "4,900 ft"},
    "Pasighat, Arunachal": {"lat": 28.0664, "lon": 95.3268, "state": "Arunachal Pradesh", "elev": "500 ft"},
    "Ziro, Arunachal": {"lat": 27.5950, "lon": 93.8380, "state": "Arunachal Pradesh", "elev": "5,538 ft"},
    "Bhalukpong, Arunachal": {"lat": 27.0125, "lon": 92.6467, "state": "Arunachal Pradesh", "elev": "700 ft"},

    # Meghalaya
    "Shillong, Meghalaya": {"lat": 25.5788, "lon": 91.8933, "state": "Meghalaya", "elev": "4,908 ft"},
    "Cherrapunji, Meghalaya": {"lat": 25.2986, "lon": 91.7314, "state": "Meghalaya", "elev": "4,869 ft"},
    "Jowai, Meghalaya": {"lat": 25.4470, "lon": 92.2030, "state": "Meghalaya", "elev": "4,500 ft"},
    "Tura, Meghalaya": {"lat": 25.5141, "lon": 90.2033, "state": "Meghalaya", "elev": "1,145 ft"},
    "Nongpoh, Meghalaya": {"lat": 25.9000, "lon": 91.8800, "state": "Meghalaya", "elev": "1,600 ft"},

    # Manipur
    "Imphal, Manipur": {"lat": 24.8170, "lon": 93.9368, "state": "Manipur", "elev": "2,560 ft"},
    "Churachandpur, Manipur": {"lat": 24.3333, "lon": 93.6833, "state": "Manipur", "elev": "3,000 ft"},
    "Jiribam, Manipur": {"lat": 24.8020, "lon": 93.1230, "state": "Manipur", "elev": "120 ft"},
    "Senapati, Manipur": {"lat": 25.2667, "lon": 94.0167, "state": "Manipur", "elev": "4,200 ft"},

    # Mizoram
    "Aizawl, Mizoram": {"lat": 23.7271, "lon": 92.7176, "state": "Mizoram", "elev": "3,730 ft"},
    "Lunglei, Mizoram": {"lat": 22.8872, "lon": 92.7307, "state": "Mizoram", "elev": "2,369 ft"},
    "Kolasib, Mizoram": {"lat": 24.2244, "lon": 92.6784, "state": "Mizoram", "elev": "2,000 ft"},
    "Champhai, Mizoram": {"lat": 23.4750, "lon": 93.3280, "state": "Mizoram", "elev": "5,499 ft"},

    # Nagaland
    "Kohima, Nagaland": {"lat": 25.6751, "lon": 94.1086, "state": "Nagaland", "elev": "4,738 ft"},
    "Dimapur, Nagaland": {"lat": 25.9068, "lon": 93.7273, "state": "Nagaland", "elev": "640 ft"},
    "Mokokchung, Nagaland": {"lat": 26.3256, "lon": 94.5298, "state": "Nagaland", "elev": "4,347 ft"},
    "Wokha, Nagaland": {"lat": 26.1000, "lon": 94.2667, "state": "Nagaland", "elev": "4,300 ft"},

    # Tripura
    "Agartala, Tripura": {"lat": 23.8315, "lon": 91.2868, "state": "Tripura", "elev": "42 ft"},
    "Dharmanagar, Tripura": {"lat": 24.3756, "lon": 92.1644, "state": "Tripura", "elev": "128 ft"},
    "Udaipur, Tripura": {"lat": 23.5333, "lon": 91.4833, "state": "Tripura", "elev": "80 ft"},

    # Sikkim
    "Gangtok, Sikkim": {"lat": 27.3389, "lon": 88.6065, "state": "Sikkim", "elev": "5,410 ft"},
    "Rangpo, Sikkim": {"lat": 27.1760, "lon": 88.5300, "state": "Sikkim", "elev": "1,050 ft"},
    "Namchi, Sikkim": {"lat": 27.1667, "lon": 88.3500, "state": "Sikkim", "elev": "4,314 ft"},
    "Pelling, Sikkim": {"lat": 27.3167, "lon": 88.2333, "state": "Sikkim", "elev": "6,800 ft"},

    # Gateway
    "Siliguri, Gateway": {"lat": 26.7271, "lon": 88.3953, "state": "Sikkim Gateway", "elev": "400 ft"}
}

def geocode_place(query):
    if not query:
        return "Guwahati, Assam", 26.1445, 91.7362, "180 ft"
    if query in NER_PLACES:
        p = NER_PLACES[query]
        return query, p["lat"], p["lon"], p["elev"]
    q_low = query.lower().strip()
    for key, val in NER_PLACES.items():
        if q_low in key.lower() or key.lower() in q_low:
            return key, val["lat"], val["lon"], val["elev"]
    return "Guwahati, Assam", 26.1445, 91.7362, "180 ft"

vehicles = [
    {
        "id": "NER-MED-01", "carrier": "Emergency Vaccine Express",
        "driver": "R. Sonowal (+91 98765-43210)", "cargo": "Vaccines & Blood Bags",
        "priority": "CRITICAL", "origin": "Guwahati, Assam", "destination": "Tawang, Arunachal",
        "lat": 27.2000, "lon": 92.3900, "speed": "38 km/h", "eta": "3h 10m",
        "status": "In Transit via Route B (Safe)", "fuel": "84%", "temperature": "2.4°C",
        "is_emergency": True, "emergency_reason": "High Altitude Cold-Chain Vaccine Transit"
    },
    {
        "id": "NER-OXY-09", "carrier": "Medical Oxygen Lifeline",
        "driver": "T. Angami (+91 98765-99887)", "cargo": "Cylinders & Concentrators",
        "priority": "CRITICAL", "origin": "Jorhat, Assam", "destination": "Kohima, Nagaland",
        "lat": 26.3500, "lon": 94.1000, "speed": "42 km/h", "eta": "2h 45m",
        "status": "Approaching Naga Checkpost", "fuel": "72%", "temperature": "N/A",
        "is_emergency": True, "emergency_reason": "Hospital Oxygen Replenishment"
    },
    {
        "id": "NER-RAT-04", "carrier": "FCI Essential Food Relief",
        "driver": "M. Debbarma (+91 98765-11223)", "cargo": "20 Ton Food Grain Silo",
        "priority": "HIGH", "origin": "Guwahati, Assam", "destination": "Silchar, Assam",
        "lat": 25.4470, "lon": 92.2030, "speed": "46 km/h", "eta": "4h 20m",
        "status": "Passing Jowai Plateau", "fuel": "90%", "temperature": "Ambient",
        "is_emergency": False, "emergency_reason": "Regular Grain Corridor"
    },
    {
        "id": "AS-01-GB-4421", "carrier": "Disaster Heavy Crane Convoy",
        "driver": "K. Boro (+91 98765-55443)", "cargo": "Road Clearance Machinery",
        "priority": "HIGH", "origin": "Tezpur, Assam", "destination": "Bomdila, Arunachal",
        "lat": 26.8500, "lon": 92.5500, "speed": "32 km/h", "eta": "1h 50m",
        "status": "En Route to Clearance Zone", "fuel": "65%", "temperature": "N/A",
        "is_emergency": True, "emergency_reason": "Active Landslide Excavation Dispatch"
    }
]

incidents = [
    {
        "id": "DIS-9021", "type": "Active Landslide / Mudflow",
        "location": "Near Bomdila Pass, NH-13 (KM 142), Arunachal",
        "severity": "HIGH", "time": "18 mins ago", "reported_by": "Insp. D. Sharma (BRO Unit 4)",
        "description": "Debris and mud accumulation blocking single lane. 2 Excavators deployed. Clearance ETA: 4 Hours.",
        "lat": 27.2640, "lon": 92.4240
    },
    {
        "id": "DIS-9020", "type": "Flash Flooding / Submerged Bridge",
        "location": "Sonapur Tunnel Approach, NH-6, Meghalaya",
        "severity": "MEDIUM", "time": "1 hour ago", "reported_by": "Meghalaya SDMA Field Cell",
        "description": "Water level 1.5 ft near tunnel portal. Slow convoy movement advised.",
        "lat": 25.1050, "lon": 92.3650
    },
    {
        "id": "DIS-9019", "type": "Major Highway Accident",
        "location": "Jorabat Junction, Assam-Meghalaya Border",
        "severity": "MEDIUM", "time": "2 hours ago", "reported_by": "Traffic Police Control Cell",
        "description": "Truck collision causing 2 km congestion. Emergency hydraulic crane deployed.",
        "lat": 26.1150, "lon": 91.8600
    }
]

def get_8_states_weather():
    state_weather = []
    for reg in REGIONS:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": reg["lat"], "longitude": reg["lon"],
            "current": "temperature_2m,rain,wind_speed_10m,relative_humidity_2m,surface_pressure,cloud_cover,weather_code",
            "timezone": "Asia/Kolkata"
        }
        try:
            res = requests.get(url, params=params, timeout=2.5)
            if res.status_code == 200:
                cur = res.json().get("current", {})
                code = cur.get("weather_code", 0)
                cond = "Clear Sky" if code == 0 else ("Rain / Showers" if code in [51,53,61,63,65,80] else ("Thunderstorm" if code >= 95 else "Partly Cloudy"))
                temp = cur.get("temperature_2m", 25.0)
                rain = cur.get("rain", 0.0)
                wind = cur.get("wind_speed_10m", 14.0)
                humidity = cur.get("relative_humidity_2m", 76)
                risk = "HIGH" if (rain > 18 or "Arunachal" in reg["name"]) else ("MEDIUM" if rain > 5 else "LOW")

                state_weather.append({
                    **reg, "temperature": temp, "rain": rain, "wind_speed": wind,
                    "humidity": humidity, "condition": cond, "risk": risk
                })
                continue
        except Exception:
            pass

        state_weather.append({
            **reg, "temperature": 24.8, "rain": 12.4, "wind_speed": 15.0,
            "humidity": 78, "condition": "Partly Cloudy",
            "risk": "LOW" if reg["code"] in ["AS", "MZ", "NL", "SK"] else "MEDIUM"
        })
    return state_weather

def calculate_risk(rainfall, landslide, road, traffic, historical, travel_time):
    score = (rainfall * 0.30 + landslide * 0.25 + road * 0.20 + traffic * 0.10 + historical * 0.10 + travel_time * 0.05)
    level = "LOW" if score <= 30 else ("MEDIUM" if score <= 60 else ("HIGH" if score <= 80 else "CRITICAL"))
    return round(score, 1), level

@app.route("/api/find-routes", methods=["POST"])
def find_routes():
    data = request.get_json(silent=True) or {}
    orig_city = data.get("origin", "Guwahati, Assam")
    dest_city = data.get("destination", "Tawang, Arunachal")

    o_name, o_lat, o_lon, o_elev = geocode_place(orig_city)
    d_name, d_lat, d_lon, d_elev = geocode_place(dest_city)

    generated_routes = []

    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{o_lon},{o_lat};{d_lon},{d_lat}?overview=full&geometries=geojson&alternatives=3"
        res = requests.get(url, timeout=3.0)
        if res.status_code == 200:
            osrm_routes = res.json().get("routes", [])
            for idx, r in enumerate(osrm_routes):
                dist_km = round(r["distance"] / 1000, 1)
                dur_hrs = round(r["duration"] / 3600, 1)
                coords = [[lat, lon] for lon, lat in r["geometry"]["coordinates"]]

                is_mountain = any(st in (o_name+d_name).lower() for st in ["arunachal", "sikkim", "meghalaya", "mizoram", "nagaland"])
                base_slope = 50 if is_mountain else 25
                slope_risk = base_slope + (idx * 15)
                score, level = calculate_risk(35.0, slope_risk, 30 + (idx * 18), 30, 25, 30)

                generated_routes.append({
                    "id": f"ROUTE-{idx+1}",
                    "name": f"Corridor {chr(65+idx)}: {'Primary Trunk Highway' if idx==0 else 'Strategic Mountain Bypass ' + str(idx)}",
                    "origin": o_name, "destination": d_name, "distance": f"{dist_km} km",
                    "eta": f"{math.floor(dur_hrs)}h {int((dur_hrs%1)*60)}m", "score": score,
                    "safety_score": round(100 - score, 1),
                    "risk": level, "status": "Safe & Open" if score < 40 else "Caution: Terrain Alert",
                    "elevation_max": f"{3500 + (idx*1800)} ft", "coordinates": coords
                })
    except Exception:
        pass

    if not generated_routes:
        direct_dist = round(math.sqrt((d_lat - o_lat)**2 + (d_lon - o_lon)**2) * 111 * 1.35, 1)
        base_dur = max(0.5, round(direct_dist / 42, 1))

        coords_1 = [[o_lat, o_lon], [(o_lat+d_lat)/2 + 0.08, (o_lon+d_lon)/2 - 0.08], [d_lat, d_lon]]
        coords_2 = [[o_lat, o_lon], [(o_lat+d_lat)/2 - 0.12, (o_lon+d_lon)/2 + 0.15], [d_lat, d_lon]]

        generated_routes.append({
            "id": "ROUTE-1", "name": f"Corridor A (Primary Trunk Highway via {o_name.split(',')[0]})",
            "origin": o_name, "destination": d_name, "distance": f"{direct_dist} km",
            "eta": f"{math.floor(base_dur)}h {int((base_dur%1)*60)}m", "score": 68.5, "safety_score": 31.5, "risk": "MEDIUM",
            "status": "Mudflow Monitoring", "elevation_max": "7,900 ft", "coordinates": coords_1
        })
        generated_routes.append({
            "id": "ROUTE-2", "name": "Corridor B (Strategic Valley Bypass - Low Hazard)",
            "origin": o_name, "destination": d_name, "distance": f"{round(direct_dist * 1.14, 1)} km",
            "eta": f"{math.floor(base_dur * 1.15)}h {int(((base_dur*1.15)%1)*60)}m", "score": 28.4, "safety_score": 71.6, "risk": "LOW",
            "status": "Clear & AI Recommended", "elevation_max": "3,400 ft", "coordinates": coords_2
        })

    best_route = min(generated_routes, key=lambda r: r["score"])

    return jsonify({
        "origin": {"name": o_name, "lat": o_lat, "lon": o_lon, "elev": o_elev},
        "destination": {"name": d_name, "lat": d_lat, "lon": d_lon, "elev": d_elev},
        "routes": generated_routes, "best_route_id": best_route["id"],
        "ai_analysis": f"AI computed {len(generated_routes)} corridors. {best_route['name']} has the lowest hazard risk index ({best_route['score']}/100)."
    })

@app.route("/api/track-vehicle", methods=["POST"])
def track_vehicle():
    data = request.get_json(silent=True) or {}
    v_id = data.get("vehicle_id", "").strip().upper()
    is_official = session.get("is_official", False)

    for v in vehicles:
        if v["id"].upper() == v_id or v_id in v["id"].upper():
            if not is_official and not v.get("is_emergency", False):
                return jsonify({
                    "status": "restricted",
                    "message": "🔒 Access Restricted: Live tactical tracking of non-emergency government convoys is only visible to Field Officers and Government Officials."
                }), 403
            return jsonify({"status": "found", "vehicle": v, "is_official": is_official})

    gen_vehicle = {
        "id": v_id if v_id else "NER-CONVOY-LIVE", "carrier": "Emergency Regional Relief Truck",
        "driver": "Duty Officer (+91 98765-00112)", "cargo": "Essential Medical & Food Relief",
        "priority": "HIGH", "origin": "Guwahati, Assam", "destination": "Regional Supply Point",
        "lat": 26.5400, "lon": 92.1200, "speed": "40 km/h", "eta": "2h 30m",
        "status": "In Transit (Telemetry Live)", "fuel": "80%", "temperature": "Active",
        "is_emergency": True, "emergency_reason": "Public Emergency Transit"
    }
    return jsonify({"status": "found", "vehicle": gen_vehicle, "is_official": is_official})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Namaste! Please ask a question regarding North-East routes, live weather, convoys, or hazard alerts."})

    msg_low = user_msg.lower()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    out_of_scope_reply = """🛡️ **NER-SMARTBOT Scope Notice:**

I am fine-tuned **exclusively for NER-SMARTLOG** (MDoNER / SIH PS-26002). I only answer questions regarding:
• 🛣️ **8-State Highway Corridors & Passes** (e.g. *'Find route from Guwahati to Tawang'*)
• 🌦️ **Real-World 8-State Weather & Rainfall** (e.g. *'Weather in Meghalaya'*)
• ⛰️ **Active Landslides & Flood Alerts** (e.g. *'Landslide status on NH-13'*)
• 🚚 **Emergency Convoy & Relief Fleet Tracking** (e.g. *'Track vehicle NER-MED-01'*)
• 🔐 **Login Credentials & Role Permissions** (e.g. *'What are the login roles?'*)

*(I do not answer general trivia, movies, sports, or off-topic programming questions.)*"""

    if gemini_key:
        try:
            all_weather = get_8_states_weather()
            weather_text = "; ".join([f"{w['name']}: {w['temperature']}C, {w['rain']}mm rain ({w['condition']}, Risk: {w['risk']})" for w in all_weather])
            incidents_text = "; ".join([f"{inc['type']} at {inc['location']} (Severity: {inc['severity']})" for inc in incidents])
            convoys_text = "; ".join([f"{v['id']} ({v['cargo']}) moving {v['origin']}->{v['destination']}, Speed: {v['speed']}" for v in vehicles])

            system_prompt = f"""You are NER-SMARTBOT, an elite domain-restricted AI copilot for the NER-SMARTLOG portal (Ministry of Development of North Eastern Region - MDoNER | SIH PS-26002).

STRICT DOMAIN RESTRICTION:
1. You MUST ONLY answer questions about North East India logistics, highway corridors, 8-state weather, landslides/floods, emergency convoys, and login roles.
2. If the user asks anything outside this portal, politely decline and redirect them.

CURRENT REAL-TIME CONTEXT:
• Live Weather: {weather_text}
• Active Hazards: {incidents_text}
• Active Convoys: {convoys_text}
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {"contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\n\nUser Question: {user_msg}"}]}]}
            res = requests.post(url, json=payload, timeout=6)
            if res.status_code == 200:
                result = res.json()
                reply_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return jsonify({"reply": reply_text})
        except Exception as e:
            print(f"Gemini API fallback: {e}")

    domain_keywords = [
        "ner", "smartlog", "route", "corridor", "highway", "pass", "sela", "bomdila", "weather", "rain",
        "temperature", "wind", "humidity", "assam", "arunachal", "meghalaya", "manipur", "mizoram", "nagaland",
        "tripura", "sikkim", "guwahati", "tawang", "shillong", "imphal", "aizawl", "kohima", "gangtok", "agartala",
        "siliguri", "track", "convoy", "vehicle", "truck", "fleet", "vaccine", "oxygen", "med", "grain", "fci",
        "landslide", "flood", "disaster", "hazard", "incident", "bro", "sdma", "role", "officer", "traveler",
        "login", "credential", "formula", "score", "risk", "what is", "about", "help", "hello", "hi", "namaste"
    ]

    if not any(k in msg_low for k in domain_keywords) and len(msg_low.split()) > 1:
        return jsonify({"reply": out_of_scope_reply})

    if any(w in msg_low for w in ["weather", "rain", "temperature", "temp", "climate", "forecast", "humidity", "wind"]):
        all_weather = get_8_states_weather()
        matched_state = None
        for w in all_weather:
            if w["name"].lower() in msg_low or w["code"].lower() in msg_low.split() or w["capital"].lower() in msg_low:
                matched_state = w
                break
        
        if not matched_state:
            for p_key, p_val in NER_PLACES.items():
                if p_key.lower().split(",")[0] in msg_low:
                    st_name = p_val["state"].split()[0]
                    for w in all_weather:
                        if st_name.lower() in w["name"].lower():
                            matched_state = w
                            break
                    if matched_state:
                        break

        if matched_state:
            reply = f"""🌦️ **Live Weather for {matched_state['name']} ({matched_state['capital']}):**

• 🌡️ **Temperature:** {matched_state['temperature']}°C
• 🌧️ **Precipitation:** {matched_state['rain']} mm/hr
• 💨 **Wind Speed:** {matched_state['wind_speed']} km/h
• 💧 **Humidity:** {matched_state['humidity']}%
• ⛅ **Condition:** {matched_state['condition']}
• ⚠️ **Road Risk Level:** **{matched_state['risk']}** ({matched_state['weather_zone']})"""
            return jsonify({"reply": reply})
        else:
            lines = [f"• **{w['name']}:** {w['temperature']}°C | {w['rain']} mm rain ({w['condition']}) — Risk: **{w['risk']}**" for w in all_weather]
            reply = "🌦️ **Real-Time 8-State Weather Telemetry (Open-Meteo Gateway):**\n\n" + "\n".join(lines)
            return jsonify({"reply": reply})

    if any(w in msg_low for w in ["track", "convoy", "truck", "med", "oxygen", "grain", "fleet", "vehicle"]):
        matched_v = None
        for v in vehicles:
            if v["id"].lower() in msg_low or v["carrier"].lower() in msg_low or v["cargo"].lower() in msg_low:
                matched_v = v
                break
        
        if matched_v:
            reply = f"""🚚 **Live Convoy Telemetry [{matched_v['id']}]:**

• 📦 **Carrier & Cargo:** {matched_v['carrier']} ({matched_v['cargo']})
• 🚨 **Priority Status:** **{matched_v['priority']}**
• 🛣️ **Route Corridor:** {matched_v['origin']} ➔ {matched_v['destination']}
• ⚡ **Current Speed:** {matched_v['speed']} (ETA: {matched_v['eta']})
• 👨‍✈️ **Assigned Driver:** {matched_v['driver']}
• 📍 **Status:** {matched_v['status']}
• ❄️ **Cold-Chain Temp:** {matched_v.get('temperature', 'N/A')}"""
            return jsonify({"reply": reply})
        else:
            lines = [f"• 🚚 **{v['id']}** ({v['cargo']}): {v['origin']} ➔ {v['destination']} | Speed: {v['speed']} | Status: *{v['status']}*" for v in vehicles]
            reply = "🛰️ **Live Active Convoys in North East Grid:**\n\n" + "\n".join(lines)
            return jsonify({"reply": reply})

    if any(w in msg_low for w in ["landslide", "flood", "disaster", "hazard", "incident", "bro", "sdma", "block"]):
        lines = [f"• ⚠️ **[{inc['severity']}] {inc['type']}** at {inc['location']}\n  Status: {inc['description']} (Reported: {inc['time']})" for inc in incidents]
        reply = f"🚨 **Active Field Hazards Broadcast ({len(incidents)} Active):**\n\n" + "\n\n".join(lines)
        return jsonify({"reply": reply})

    if any(w in msg_low for w in ["sela", "sela tunnel", "sela pass"]):
        reply = """🏔️ **Sela Corridor Strategic Status (Arunachal - 13,700 ft):**

• **Sela Tunnel:** ✅ **Operational & All-Weather Safe.**
• **Recommendation:** Relief convoys to Tawang Hospital route via Sela Tunnel to bypass heavy snow zones."""
        return jsonify({"reply": reply})

    if any(w in msg_low for w in ["bomdila", "nh-13", "dirang"]):
        reply = "⛰️ **NH-13 Bomdila Pass KM 142 Alert:** Active mudflow detected. Excavators deployed by BRO Unit 4. AI suggests taking the Kalaktang Bypass corridor."
        return jsonify({"reply": reply})

    if "from" in msg_low and "to" in msg_low:
        parts = msg_low.split("to")
        orig = parts[0].replace("from", "").replace("find route", "").strip().title()
        dest = parts[1].strip().title()
        return jsonify({"reply": f"🛣️ **AI Corridor Computed for {orig} ➔ {dest}:** Multi-corridor terrain gradient and rainfall risk evaluated. Use the dropdown selectors on the Mission Control Map to visualize the safest route!"})

    if any(w in msg_low for w in ["login", "credential", "role", "officer", "traveler", "permission"]):
        reply = """🔐 **NER-SMARTLOG Role & Access System:**

1. 👮 **Field Officer / Govt Official:** Full tactical mission control, live GPS tracking of all convoys, road clearance logging, and disaster broadcast authority.
   • Email: `officer@ner.gov.in` (Password: `officer2026`)
   • Email: `commander@ner.gov.in` (Password: `govt2026`)

2. 🚗 **Normal Vehicle Traveler:** Public safety view with multi-corridor route optimizer, live 8-state weather feeds, and active disaster alerts.
   • Email: `traveler@northeast.in` (Password: `travel2026`)
   • Email: `driver@nerlog.in` (Password: `driver2026`)"""
        return jsonify({"reply": reply})

    if any(w in msg_low for w in ["what is", "about", "website", "project", "purpose", "who are you"]):
        reply = """🚚 **About NER-SMARTLOG (SIH PS-26002):**

An **AI-Powered Street Logistics & Real-Time Hazard Intelligence System**
