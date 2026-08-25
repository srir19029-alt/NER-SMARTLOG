import os
import math
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from jinja2 import ChoiceLoader, FileSystemLoader
from chatbot import ask_gemini

# Automatic path detection
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = "ner-smartlog-secret-key-2026"

# FIX: Automatically search both 'templates/' subfolder AND current directory
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    FileSystemLoader(BASE_DIR),
    FileSystemLoader('.')
])

# ==========================================================
# 1. 8 NORTH-EASTERN STATES REGIONAL DATA
# ==========================================================
regions = [
    {
        "name": "Assam", "code": "AS", "capital": "Dispur / Guwahati",
        "lat": 26.1445, "lon": 91.7362, "routes": 34,
        "accessibility": "95%", "weather_zone": "Brahmaputra Valley Corridor",
        "key_hubs": ["Guwahati Hub", "Tezpur Depot", "Silchar Gate", "Dibrugarh Center"]
    },
    {
        "name": "Arunachal Pradesh", "code": "AR", "capital": "Itanagar",
        "lat": 27.0844, "lon": 93.6053, "routes": 18,
        "accessibility": "58%", "weather_zone": "High Himalayan Landslide Prone",
        "key_hubs": ["Tawang Base", "Bomdila Pass", "Dirang Valley", "Pasighat"]
    },
    {
        "name": "Meghalaya", "code": "ML", "capital": "Shillong",
        "lat": 25.5788, "lon": 91.8933, "routes": 22,
        "accessibility": "78%", "weather_zone": "Heavy Rain & Dense Cloud Fog",
        "key_hubs": ["Shillong Peak", "Jowai Transit", "Cherrapunji Station", "Nongpoh"]
    },
    {
        "name": "Manipur", "code": "MN", "capital": "Imphal",
        "lat": 24.8170, "lon": 93.9368, "routes": 16,
        "accessibility": "72%", "weather_zone": "Valley Transport Corridor",
        "key_hubs": ["Imphal Central", "Jiribam Railhead", "Senapati Checkpost"]
    },
    {
        "name": "Mizoram", "code": "MZ", "capital": "Aizawl",
        "lat": 23.7271, "lon": 92.7176, "routes": 14,
        "accessibility": "88%", "weather_zone": "Southern Hill Ridge Corridor",
        "key_hubs": ["Aizawl Civil Depot", "Kolasib Junction", "Vairengte Gate"]
    },
    {
        "name": "Nagaland", "code": "NL", "capital": "Kohima",
        "lat": 25.6751, "lon": 94.1086, "routes": 15,
        "accessibility": "86%", "weather_zone": "Naga Hills Transit Route",
        "key_hubs": ["Kohima Base", "Dimapur Logistics Silo", "Mokokchung"]
    },
    {
        "name": "Tripura", "code": "TR", "capital": "Agartala",
        "lat": 23.8315, "lon": 91.2868, "routes": 12,
        "accessibility": "82%", "weather_zone": "Plains Highway Access",
        "key_hubs": ["Agartala Dry Port", "Dharmanagar Depot", "Udaipur Hub"]
    },
    {
        "name": "Sikkim", "code": "SK", "capital": "Gangtok",
        "lat": 27.3389, "lon": 88.6065, "routes": 10,
        "accessibility": "90%", "weather_zone": "Teesta River Highway Sector",
        "key_hubs": ["Gangtok Terminal", "Rangpo Checkpoint", "Sevoke Corridor"]
    }
]

# ==========================================================
# 2. NER GEOGRAPHIC GAZETTEER
# ==========================================================
NER_PLACES = {
    "guwahati": {"name": "Guwahati, Assam", "lat": 26.1445, "lon": 91.7362, "state": "Assam", "elev": "180 ft"},
    "dispur": {"name": "Dispur, Assam", "lat": 26.1408, "lon": 91.7907, "state": "Assam", "elev": "185 ft"},
    "silchar": {"name": "Silchar, Assam", "lat": 24.8333, "lon": 92.7789, "state": "Assam", "elev": "82 ft"},
    "tezpur": {"name": "Tezpur, Assam", "lat": 26.6338, "lon": 92.8000, "state": "Assam", "elev": "157 ft"},
    "dibrugarh": {"name": "Dibrugarh, Assam", "lat": 27.4728, "lon": 94.9120, "state": "Assam", "elev": "354 ft"},
    "jorhat": {"name": "Jorhat, Assam", "lat": 26.7509, "lon": 94.2037, "state": "Assam", "elev": "380 ft"},
    "nagaon": {"name": "Nagaon, Assam", "lat": 26.3452, "lon": 92.6840, "state": "Assam", "elev": "220 ft"},
    "bhalukpong": {"name": "Bhalukpong, Arunachal", "lat": 27.0125, "lon": 92.6467, "state": "Arunachal Pradesh", "elev": "700 ft"},
    "bomdila": {"name": "Bomdila, Arunachal", "lat": 27.2640, "lon": 92.4240, "state": "Arunachal Pradesh", "elev": "7,923 ft"},
    "dirang": {"name": "Dirang, Arunachal", "lat": 27.3556, "lon": 92.2389, "state": "Arunachal Pradesh", "elev": "4,900 ft"},
    "tawang": {"name": "Tawang, Arunachal", "lat": 27.5860, "lon": 91.8590, "state": "Arunachal Pradesh", "elev": "10,000 ft"},
    "itanagar": {"name": "Itanagar, Arunachal", "lat": 27.0844, "lon": 93.6053, "state": "Arunachal Pradesh", "elev": "2,460 ft"},
    "pasighat": {"name": "Pasighat, Arunachal", "lat": 28.0664, "lon": 95.3268, "state": "Arunachal Pradesh", "elev": "500 ft"},
    "shillong": {"name": "Shillong, Meghalaya", "lat": 25.5788, "lon": 91.8933, "state": "Meghalaya", "elev": "4,908 ft"},
    "cherrapunji": {"name": "Cherrapunji (Sohra), Meghalaya", "lat": 25.2986, "lon": 91.7314, "state": "Meghalaya", "elev": "4,869 ft"},
    "jowai": {"name": "Jowai, Meghalaya", "lat": 25.4470, "lon": 92.2030, "state": "Meghalaya", "elev": "4,500 ft"},
    "tura": {"name": "Tura, Meghalaya", "lat": 25.5141, "lon": 90.2033, "state": "Meghalaya", "elev": "1,145 ft"},
    "imphal": {"name": "Imphal, Manipur", "lat": 24.8170, "lon": 93.9368, "state": "Manipur", "elev": "2,560 ft"},
    "churachandpur": {"name": "Churachandpur, Manipur", "lat": 24.3333, "lon": 93.6833, "state": "Manipur", "elev": "3,000 ft"},
    "jiribam": {"name": "Jiribam, Manipur", "lat": 24.8020, "lon": 93.1230, "state": "Manipur", "elev": "120 ft"},
    "aizawl": {"name": "Aizawl, Mizoram", "lat": 23.7271, "lon": 92.7176, "state": "Mizoram", "elev": "3,730 ft"},
    "lunglei": {"name": "Lunglei, Mizoram", "lat": 22.8872, "lon": 92.7307, "state": "Mizoram", "elev": "2,369 ft"},
    "kolasib": {"name": "Kolasib, Mizoram", "lat": 24.2244, "lon": 92.6784, "state": "Mizoram", "elev": "2,000 ft"},
    "kohima": {"name": "Kohima, Nagaland", "lat": 25.6751, "lon": 94.1086, "state": "Nagaland", "elev": "4,738 ft"},
    "dimapur": {"name": "Dimapur, Nagaland", "lat": 25.9068, "lon": 93.7273, "state": "Nagaland", "elev": "640 ft"},
    "mokokchung": {"name": "Mokokchung, Nagaland", "lat": 26.3256, "lon": 94.5298, "state": "Nagaland", "elev": "4,347 ft"},
    "agartala": {"name": "Agartala, Tripura", "lat": 23.8315, "lon": 91.2868, "state": "Tripura", "elev": "42 ft"},
    "dharmanagar": {"name": "Dharmanagar, Tripura", "lat": 24.3756, "lon": 92.1644, "state": "Tripura", "elev": "128 ft"},
    "udaipur": {"name": "Udaipur, Tripura", "lat": 23.5333, "lon": 91.4833, "state": "Tripura", "elev": "80 ft"},
    "gangtok": {"name": "Gangtok, Sikkim", "lat": 27.3389, "lon": 88.6065, "state": "Sikkim", "elev": "5,410 ft"},
    "rangpo": {"name": "Rangpo, Sikkim", "lat": 27.1760, "lon": 88.5300, "state": "Sikkim", "elev": "1,050 ft"},
    "namchi": {"name": "Namchi, Sikkim", "lat": 27.1667, "lon": 88.3500, "state": "Sikkim", "elev": "4,314 ft"},
    "siliguri": {"name": "Siliguri, Gateway", "lat": 26.7271, "lon": 88.3953, "state": "Sikkim Gateway", "elev": "400 ft"}
}

def geocode_place(query):
    if not query:
        return "Guwahati, Assam", 26.1445, 91.7362, "180 ft"
    q = query.lower().strip()
    for key, val in NER_PLACES.items():
        if key in q or q in key:
            return val["name"], val["lat"], val["lon"], val["elev"]
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&countrycodes=in&limit=1"
        headers = {"User-Agent": "NER-SMARTLOG-MDoNER-System/4.0"}
        r = requests.get(url, headers=headers, timeout=2)
        if r.status_code == 200:
            res = r.json()
            if res and len(res) > 0:
                return res[0]["display_name"].split(",")[0] + ", NER", float(res[0]["lat"]), float(res[0]["lon"]), "Variable Terrain"
    except Exception:
        pass
    return "Guwahati, Assam", 26.1445, 91.7362, "180 ft"

# ==========================================================
# 3. CONVOY FLEET & GROUND INCIDENTS
# ==========================================================
vehicles = [
    {
        "id": "NER-MED-01", "carrier": "Emergency Vaccine Express",
        "driver": "R. Sonowal (+91 98765-43210)", "cargo": "Vaccines & Blood Bags",
        "priority": "CRITICAL", "origin": "Guwahati Depot", "destination": "Tawang Base Hospital",
        "lat": 27.2000, "lon": 92.3900, "speed": "38 km/h", "eta": "3h 10m",
        "status": "In Transit via Route B (Safe)", "fuel": "84%", "temp_controlled": "2.4°C"
    },
    {
        "id": "NER-OXY-09", "carrier": "Medical Oxygen Lifeline",
        "driver": "T. Angami (+91 98765-99887)", "cargo": "Cylinders & Concentrators",
        "priority": "CRITICAL", "origin": "Jorhat Storage", "destination": "Kohima Medical Facility",
        "lat": 26.3500, "lon": 94.1000, "speed": "42 km/h", "eta": "2h 45m",
        "status": "Approaching Checkpost", "fuel": "72%", "temp_controlled": "N/A"
    },
    {
        "id": "NER-RAT-04", "carrier": "FCI Essential Food Relief",
        "driver": "M. Debbarma (+91 98765-11223)", "cargo": "20 Ton Food Grain Silo",
        "priority": "HIGH", "origin": "Guwahati Silo", "destination": "Silchar Relief Hub",
        "lat": 25.4470, "lon": 92.2030, "speed": "46 km/h", "eta": "4h 20m",
        "status": "Passing Jowai Plateau", "fuel": "90%", "temp_controlled": "Ambient"
    },
    {
        "id": "AS-01-GB-4421", "carrier": "Disaster Heavy Crane Convoy",
        "driver": "K. Boro (+91 98765-55443)", "cargo": "Road Clearance Machinery",
        "priority": "HIGH", "origin": "Tezpur Military Base", "destination": "Bomdila Landslide Sector",
        "lat": 26.8500, "lon": 92.5500, "speed": "32 km/h", "eta": "1h 50m",
        "status": "En Route to Clearance Zone", "fuel": "65%", "temp_controlled": "N/A"
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

# ==========================================================
# 4. WEATHER TELEMETRY (OPEN-METEO)
# ==========================================================
def get_8_states_weather():
    state_weather = []
    for reg in regions:
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
                    **reg,
                    "temperature": temp, "rain": rain, "wind_speed": wind,
                    "humidity": humidity, "condition": cond, "risk": risk
                })
                continue
        except Exception:
            pass

        state_weather.append({
            **reg,
            "temperature": 24.8, "rain": 12.4, "wind_speed": 15.0,
            "humidity": 78, "condition": "Partly Cloudy",
            "risk": "LOW" if reg["code"] in ["AS", "MZ", "NL", "SK"] else "MEDIUM"
        })
    return state_weather

def calculate_risk(rainfall, landslide, road, traffic, historical, travel_time):
    score = (rainfall * 0.30 + landslide * 0.25 + road * 0.20 + traffic * 0.10 + historical * 0.10 + travel_time * 0.05)
    level = "LOW" if score <= 30 else ("MEDIUM" if score <= 60 else ("HIGH" if score <= 80 else "CRITICAL"))
    return round(score, 1), level

# ==========================================================
# 5. MULTI-ROUTE ENGINE
# ==========================================================
@app.route("/api/find-routes", methods=["POST"])
def find_routes():
    data = request.get_json(silent=True) or {}
    origin_query = data.get("origin", "Guwahati, Assam")
    dest_query = data.get("destination", "Tawang, Arunachal")

    o_name, o_lat, o_lon, o_elev = geocode_place(origin_query)
    d_name, d_lat, d_lon, d_elev = geocode_place(dest_query)

    generated_routes = []

    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{o_lon},{o_lat};{d_lon},{d_lat}?overview=full&geometries=geojson&alternatives=3"
        res = requests.get(url, timeout=3)
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
                    "name": f"Corridor {chr(65+idx)}: {'Primary Highway' if idx==0 else 'Strategic Bypass ' + str(idx)}",
                    "origin": o_name, "destination": d_name, "distance": f"{dist_km} km",
                    "eta": f"{math.floor(dur_hrs)}h {int((dur_hrs%1)*60)}m", "score": score,
                    "risk": level, "status": "Safe & Open" if score < 40 else "Caution: Mountain Terrain",
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
            "eta": f"{math.floor(base_dur)}h {int((base_dur%1)*60)}m", "score": 68.5, "risk": "MEDIUM",
            "status": "Monsoonal Mudflow Monitoring", "elevation_max": "7,900 ft", "coordinates": coords_1
        })
        generated_routes.append({
            "id": "ROUTE-2", "name": "Corridor B (Strategic Valley Bypass - Low Hazard)",
            "origin": o_name, "destination": d_name, "distance": f"{round(direct_dist * 1.14, 1)} km",
            "eta": f"{math.floor(base_dur * 1.15)}h {int(((base_dur*1.15)%1)*60)}m", "score": 28.4, "risk": "LOW",
            "status": "Clear & AI Recommended", "elevation_max": "3,400 ft", "coordinates": coords_2
        })

    best_route = min(generated_routes, key=lambda r: r["score"])

    return jsonify({
        "origin": {"name": o_name, "lat": o_lat, "lon": o_lon, "elev": o_elev},
        "destination": {"name": d_name, "lat": d_lat, "lon": d_lon, "elev": d_elev},
        "routes": generated_routes, "best_route_id": best_route["id"],
        "ai_analysis": f"AI computed {len(generated_routes)} corridors. {best_route['name']} has the lowest hazard score ({best_route['score']}/100)."
    })

# ==========================================================
# 6. VEHICLE TRACKER & SMART DIRECT-ANSWER AI CHATBOT
# ==========================================================
@app.route("/api/track-vehicle", methods=["POST"])
def track_vehicle():
    data = request.get_json(silent=True) or {}
    v_id = data.get("vehicle_id", "").strip().upper()

    for v in vehicles:
        if v["id"].upper() == v_id or v_id in v["id"].upper():
            return jsonify({"status": "found", "vehicle": v})

    gen_vehicle = {
        "id": v_id if v_id else "NER-CONVOY-LIVE", "carrier": "Emergency Regional Relief Truck",
        "driver": "Duty Officer (+91 98765-00112)", "cargo": "Essential Medical & Food Relief",
        "priority": "HIGH", "origin": "Guwahati Central Depot", "destination": "Regional Supply Point",
        "lat": 26.5400, "lon": 92.1200, "speed": "40 km/h", "eta": "2h 30m",
        "status": "In Transit (Telemetry Live)", "fuel": "80%", "temp_controlled": "Active"
    }
    return jsonify({"status": "found", "vehicle": gen_vehicle})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({
            "reply": "Namaste! Please ask me about Northeast India logistics, routes, weather, convoys, or hazards."
        })

    # Try Gemini AI first
    ai_reply = ask_gemini(
        user_msg,
        incidents=incidents,
        vehicles=vehicles
    )

    if ai_reply:
        return jsonify({
            "reply": ai_reply
        })

    # ------------------------------------------------------
    # FALLBACK CHATBOT
    # Works even if Gemini is unavailable
    # ------------------------------------------------------

    msg_low = user_msg.lower()

    if any(word in msg_low for word in [
        "hi", "hello", "namaste", "hey", "help", "start"
    ]):
        reply = (
            "👋 **Namaste! I am NER-SMARTBOT.**\n\n"
            "I can help with:\n"
            "• 🛣

    # 3. DIRECT CONVOY TRACKING PRINTED IN CHAT
    if any(w in msg_low for w in ["track", "convoy", "truck", "med", "oxygen", "grain", "fleet", "vehicle"]):
        matched_v = None
        for v in vehicles:
            if v["id"].lower() in msg_low or v["carrier"].lower() in msg_low or v["cargo"].lower() in msg_low:
                matched_v = v
                break
        
        if matched_v:
            reply = (
                f"🚚 **Live Convoy Telemetry [{matched_v['id']}]:**\n\n"
                f"• 📦 **Carrier & Cargo:** {matched_v['carrier']} ({matched_v['cargo']})\n"
                f"• 🚨 **Priority:** **{matched_v['priority']}**\n"
                f"• 🛣️ **Route:** {matched_v['origin']} ➔ {matched_v['destination']}\n"
                f"• ⚡ **Current Speed:** {matched_v['speed']} (ETA: {matched_v['eta']})\n"
                f"• 👨‍✈️ **Driver / Contact:** {matched_v['driver']}\n"
                f"• 📍 **Status:** {matched_v['status']}\n"
                f"• ❄️ **Cold-Chain Temp:** {matched_v.get('temp_controlled', 'N/A')}"
            )
        else:
            lines = [f"• 🚚 **{v['id']}** ({v['cargo']}): {v['origin']} ➔ {v['destination']} | Speed: **{v['speed']}** | Status: *{v['status']}*" for v in vehicles]
            reply = "🛰️ **Live Active Convoys in North East Grid:**\n\n" + "\n".join(lines)
        return jsonify({"reply": reply})

    # 4. DIRECT DISASTER HAZARDS PRINTED IN CHAT
    if any(w in msg_low for w in ["landslide", "flood", "disaster", "hazard", "incident", "bro", "sdma", "road damage"]):
        lines = []
        for inc in incidents:
            lines.append(
                f"⚠️ **[{inc['severity']}] {inc['type']}**\n"
                f"   📍 Location: {inc['location']}\n"
                f"   🕒 Reported: {inc['time']} by {inc['reported_by']}\n"
                f"   📝 Status: {inc['description']}\n"
            )
        reply = f"🚨 **Active Field Hazards Broadcast ({len(incidents)} Active):**\n\n" + "\n".join(lines)
        return jsonify({"reply": reply})

    # 5. ROUTE COMPUTATION
    if "from" in msg_low and "to" in msg_low:
        parts = msg_low.split("to")
        orig = parts[0].replace("from", "").replace("find route", "").strip()
        dest = parts[1].strip()
        return jsonify({"reply": f"🛣️ **AI Corridor Computed for {orig.title()} ➔ {dest.title()}:** Terrain slope gradient and rainfall risk evaluated. Check the Mission Control GIS Map for the safest corridor!"})

    # 6. PASSES & CORRIDORS
    if any(w in msg_low for w in ["tawang", "bomdila", "arunachal", "sela", "nh-13"]):
        return jsonify({"reply": "⛰️ **Arunachal High-Altitude Alert:** NH-13 near Bomdila Pass KM 142 has **Active Mudflow** (Risk: HIGH). AI recommends taking the **Sela Tunnel / Kalaktang Valley Bypass**."})

    # 7. ABOUT & PURPOSE
    if any(w in msg_low for w in ["what is", "about", "website", "project", "work", "purpose", "who are you", "tell me"]):
        return jsonify({"reply": (
            "🚚 **About NER-SMARTLOG (SIH PS-26002):**\n\n"
            "This portal is an **AI-powered Street Logistics & Hazard Intelligence System** for **MDoNER** (Ministry of Development of North Eastern Region).\n\n"
            "**Key Capabilities:**\n"
            "• 🛣️ **Predictive Route Engine:** Calculates multi-corridor bypasses using live landslide & rain risk scores.\n"
            "• 🌦️ **8-State Weather:** Real-world weather telemetry across Assam, Arunachal, Meghalaya, Manipur, Mizoram, Nagaland, Tripura, and Sikkim.\n"
            "• 🛰️ **Convoy GPS Tracker:** Live tracking for emergency vaccine (`NER-MED-01`), oxygen (`NER-OXY-09`), and food trucks.\n"
            "• 🚨 **BRO Incident Terminal:** Real-time damage reporting and road clearance ETAs."
        )})

    # 8. RISK SCORE FORMULA
    if any(w in msg_low for w in ["risk", "formula", "score", "calculate", "algorithm"]):
        return jsonify({"reply": (
            "📐 **Hazard Risk Index Formula:**\n\n"
            "`Score = (0.30 x Rain) + (0.25 x Landslide_Slope) + (0.20 x Road_Passability) + (0.10 x Traffic) + (0.10 x History) + (0.05 x Elevation)`\n\n"
            "• **0–30:** LOW (Clear)\n• **31–60:** MEDIUM (Caution)\n• **61–80:** HIGH (Hazard)\n• **81–100:** CRITICAL (Auto-Reroute Triggered)"
        )})

    # 9. GREETINGS & DEFAULT
    return jsonify({"reply": (
        "👋 **Namaste! I am NER-SMARTBOT**, your AI Logistics & Hazard Assistant for North East India.\n\n"
        "Ask me anything:\n"
        "• 🌦️ *'Weather in Meghalaya'* or *'Weather in Assam'*\n"
        "• 🚚 *'Track vehicle NER-MED-01'*\n"
        "• 🚨 *'Show active landslide hazards'*\n"
        "• 🛣️ *'Find route from Guwahati to Tawang'*\n"
        "• 📊 *'How does the risk score work?'*"
    )})

@app.route("/submit-disaster-report", methods=["POST"])
def submit_disaster_report():
    new_inc = {
        "id": f"DIS-{len(incidents) + 9021}",
        "type": request.form.get("incident_type", "Active Landslide"),
        "location": f"{request.form.get('location', 'Himalayan Pass')}, {request.form.get('state', 'NER')}",
        "severity": request.form.get("severity", "HIGH"),
        "time": "Just now (Verified Ground Report)",
        "reported_by": f"{request.form.get('officer_name', 'Field Officer')} ({request.form.get('agency', 'BRO')})",
        "description": request.form.get("description", ""),
        "lat": 27.2640, "lon": 92.4240
    }
    incidents.insert(0, new_inc)
    return redirect(url_for("home"))

# ==========================================================
# 7. ROUTING & CONTROLLERS
# ==========================================================
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        session["user"] = request.form.get("username", "Field Officer")
        session["role"] = request.form.get("role", "Field Patrol Officer (BRO)")
        session["show_vehicle_modal"] = True
        return redirect(url_for("home"))
    return render_template("index.html", is_login=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login_page"))

    states_weather = get_8_states_weather()
    show_modal = session.pop("show_vehicle_modal", False)

    return render_template(
        "index.html",
        is_login=False,
        user=session.get("user", "Duty Officer"),
        role=session.get("role", "Command Officer"),
        show_vehicle_modal=show_modal,
        states_weather=states_weather,
        vehicles=vehicles,
        incidents=incidents,
        places=NER_PLACES,
        timestamp=datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 NER-SMARTLOG Mission Control running on http://127.0.0.1:{port}")
    app.run(debug=True, port=port)
