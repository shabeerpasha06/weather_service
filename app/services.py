from typing import Any, Dict

import httpx
from fastapi import HTTPException, status

from .config import settings
from .utils import SimpleTTLCache

# initialize the cache (module-level so it's reused across imports)
_cache = SimpleTTLCache(max_size=settings.CACHE_MAX_SIZE, ttl_seconds=settings.CACHE_TTL_SECONDS)


async def fetch_weather(
    client: httpx.AsyncClient, city: str, unit: str
) -> Dict[str, Any]:
    """
    Fetch weather data for `city` in unit mapping specified by `unit` (centigrade/fahrenheit/kelvin).
    Uses a small in-memory cache to reduce external calls for frequent requests.
    """

    key = f"{city.strip().lower()}|{unit}"
    cached = await _cache.get(key)
    if cached is not None:
        return cached

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": settings.UNIT_MAPPING.get(unit, "metric"),
    }

    try:
        resp = await client.get(settings.OPENWEATHER_API_URL, params=params)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error contacting weather service: {exc}",
        )

    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )

    if resp.status_code >= 400:
        # bubble up useful message
        text = resp.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External weather service error ({resp.status_code}): {text}",
        )

    payload = resp.json()

    # store cache: keep the payload as-is (caller will parse to model)
    await _cache.set(key, payload)
    return payload


def extract_relevant(payload: Dict[str, Any], requested_unit: str) -> Dict[str, Any]:
    """
    Extracts and normalizes the relevant pieces of OpenWeatherMap payload into our response dict.
    This avoids returning unnecessarily large payloads unless the 'raw' field is specifically included.
    """

    city_name = payload.get("name", "")
    sys = payload.get("sys", {})
    country = sys.get("country")

    weather_items = payload.get("weather") or []
    weather_short = {}
    if weather_items:
        first = weather_items[0]
        weather_short = {
            "main": first.get("main", ""),
            "description": first.get("description", ""),
            "icon": first.get("icon", ""),
        }

    main = payload.get("main", {})
    wind = payload.get("wind", {})

    result = {
        "city": city_name or "",
        "country": country,
        "unit": requested_unit,
        "weather": weather_short,
        "main": {
            "temp": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "temp_min": main.get("temp_min"),
            "temp_max": main.get("temp_max"),
            "pressure": main.get("pressure"),
            "humidity": main.get("humidity"),
        },
        "wind": {"speed": wind.get("speed"), "deg": wind.get("deg") if "deg" in wind else None},
        "sys": {"country": country, "sunrise": sys.get("sunrise"), "sunset": sys.get("sunset")},
        "raw": payload,
    }
    return result
