"""
Daily Weather & Air Quality Alert Service (Sendinblue + City Name)
------------------------------------------------------------------
- User only provides email + city name via front-end form
- Sends daily alerts at fixed UTC hour: 6
- Automatically finds latitude/longitude from city name
- Uses Open-Meteo + OpenAQ + Sendinblue API
"""

import os
import time
import requests
from datetime import datetime, date, timedelta
from threading import Thread
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ---------------- CONFIG ----------------
SENDINBLUE_API_KEY = os.getenv("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")  # Put your Sendinblue API key here
FROM_EMAIL = "988162001@smtp-brevo.com"                 # Must match verified sender in Sendinblue
ALERT_HOUR_UTC = 6                                    # Fixed at 6 UTC
# ----------------------------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------- FUNCTIONS ----------------
def geocode_city(city_name):
    """Convert city name to lat/lon using OpenStreetMap Nominatim"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"City '{city_name}' not found")
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon

def fetch_weather(lat, lon):
    today = date.today().isoformat()
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max,shortwave_radiation_sum",
        "timezone": "UTC",
        "start_date": today,
        "end_date": today
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    j = r.json()["daily"]
    return {
        "date": j["time"][0],
        "temp_max_c": j["temperature_2m_max"][0],
        "temp_min_c": j["temperature_2m_min"][0],
        "precip_mm": j["precipitation_sum"][0],
        "uv_index_max": j.get("uv_index_max", [None])[0],
        "radiation_w_m2": j.get("shortwave_radiation_sum", [None])[0]
    }

def fetch_pm25(lat, lon, radius_m=5000):
    now = datetime.utcnow()
    date_to = now.isoformat() + "Z"
    date_from = (now - timedelta(days=1)).isoformat() + "Z"
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": radius_m,
        "parameter": "pm25",
        "date_from": date_from,
        "date_to": date_to,
        "limit": 100
    }
    r = requests.get("https://api.openaq.org/v3/measurements", params=params, timeout=20)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    vals = [r["value"] for r in results if r.get("value") is not None]
    return sum(vals)/len(vals) if vals else None

def send_email(to_email, subject, body):
    url = "https://api.sendinblue.com/v3/smtp/email"
    headers = {
        "api-key": SENDINBLUE_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "sender": {"name": "Daily Alert", "email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body
    }
    r = requests.post(url, headers=headers, json=data, timeout=20)
    if r.status_code in [200, 201]:
        print(f"[{datetime.utcnow()}] Email sent to {to_email}")
    else:
        print(f"[{datetime.utcnow()}] Failed to send email: {r.text}")

def daily_alert_loop(email, city_name):
    """Thread: sends daily email at fixed UTC hour (6)"""
    try:
        lat, lon = geocode_city(city_name)
    except Exception as e:
        print("Geocoding error:", e)
        return
    already_sent = None
    while True:
        now = datetime.utcnow()
        if now.hour == ALERT_HOUR_UTC and already_sent != now.date():
            try:
                weather = fetch_weather(lat, lon)
                pm25 = fetch_pm25(lat, lon)
                body = f"""Hello,

Daily Weather & Air Quality Alert for {weather['date']} in {city_name} ({lat:.2f},{lon:.2f}) UTC:

- Max Temp: {weather['temp_max_c']} °C
- Min Temp: {weather['temp_min_c']} °C
- Precipitation: {weather['precip_mm']} mm
- UV Index (max): {weather['uv_index_max']}
- Solar Radiation: {weather['radiation_w_m2']} W/m²
- PM2.5 Average: {pm25 if pm25 is not None else 'N/A'} μg/m³

Have a great day!
"""
                send_email(email, f"Daily Alert {weather['date']} - {city_name}", body)
                already_sent = now.date()
            except Exception as e:
                print("Error:", e)
        time.sleep(60)

# ---------------- API ROUTE ----------------
@app.post("/subscribe")
def subscribe(email: str = Form(...), city: str = Form(...)):
    """Receive email + city name from frontend and start daily alert thread at 6 UTC"""
    thread = Thread(target=daily_alert_loop, args=(email, city))
    thread.start()
    return {"message": f"Daily alert started for {email} in {city} at {ALERT_HOUR_UTC:02d}:00 UTC"}

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)