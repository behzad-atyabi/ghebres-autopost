"""Weather data from Open-Meteo (free, no key)."""
import datetime as dt

from .common import http, log

API = "https://api.open-meteo.com/v1/forecast"


def wmo_to_kind(code):
    c = int(code)
    if c in (0, 1):
        return "sunny"
    if c == 2:
        return "partly"
    if c == 3:
        return "cloudy"
    if c in (45, 48):
        return "fog"
    if 95 <= c <= 99:
        return "storm"
    if (51 <= c <= 67) or (80 <= c <= 82):
        return "rain"
    if (71 <= c <= 77) or c in (85, 86):
        return "cloudy"
    return "partly"


def fetch(cfg, now):
    wc = cfg["weather"]
    keys = list(wc["cities"].keys())
    lats = ",".join(str(wc["cities"][k][0]) for k in keys)
    lons = ",".join(str(wc["cities"][k][1]) for k in keys)
    evening = now.hour >= 12 and wc.get("evening_mode", "tomorrow") == "tomorrow"
    day = (now.date() + dt.timedelta(days=1)) if evening else now.date()
    params = {
        "latitude": lats, "longitude": lons,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,wind_speed_10m_max",
        "timezone": cfg.get("timezone", "Europe/Nicosia"),
        "start_date": day.isoformat(), "end_date": day.isoformat(),
    }
    r = http().get(API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    data = data if isinstance(data, list) else [data]
    items = []
    sunrise = sunset = None
    for k, d in zip(keys, data):
        daily = d["daily"]
        code = daily["weather_code"][0]
        kind = wmo_to_kind(code)
        wind = daily.get("wind_speed_10m_max", [0])[0] or 0
        if kind in ("sunny", "partly") and wind >= 45:
            kind = "wind"
        items.append({
            "city": k,
            "temp": round(daily["temperature_2m_max"][0]),
            "low": round(daily["temperature_2m_min"][0]),
            "condition": kind,
        })
        if k == "lefkosa":
            sunrise = daily["sunrise"][0][-5:]
            sunset = daily["sunset"][0][-5:]
    log.info("weather for %s: %s", day, items)
    spec = {"name": f"weather_{now:%Y%m%d_%H}", "layout": "weather", "date": day.isoformat(),
            "items": items, "source": "Open-Meteo"}
    if sunrise:
        spec["sunrise"], spec["sunset"] = sunrise, sunset
    if evening:
        spec["title_tr"] = "Kuzey Kıbrıs’ta Yarın Hava Durumu"
        spec["title_en"] = "Tomorrow’s Weather in Northern Cyprus"
        spec["title_fa"] = "پیش‌بینی هوای فردا در قبرس شمالی"
    return spec, evening
