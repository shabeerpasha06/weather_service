from typing import Any

import httpx
from fastapi import Depends, FastAPI, Request, Query
from fastapi.responses import JSONResponse
from pydantic.error_wrappers import ValidationError
from starlette.middleware.cors import CORSMiddleware
import time

from .config import settings
from .schemas import CityWeatherRequest, WeatherResponse
from .services import fetch_weather, extract_relevant, _cache

app = FastAPI(
    title="Weather Service",
    description="Fetch weather by city name and unit (centigrade/fahrenheit/kelvin).",
    version="1.0.0",
)

# Allow ORIGINs for local testing - adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    # Create a single shared AsyncClient with connection limits
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    app.state.http_client = httpx.AsyncClient(timeout=10.0, limits=limits)
    # record start time for uptime reporting
    app.state.start_time = time.time()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    client = getattr(app.state, "http_client", None)
    if client:
        await client.aclose()


def get_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


@app.post("/weather", response_model=WeatherResponse, name="Get Weather")
async def get_weather(req: CityWeatherRequest, client: httpx.AsyncClient = Depends(get_client)) -> Any:
    """
    Returns weather data for the requested city and unit.
    Request model is validated with Pydantic (CityWeatherRequest).
    Response is validated and serialized using the WeatherResponse model.
    """
    payload = await fetch_weather(client=client, city=req.city, unit=req.unit.value)
    normalized = extract_relevant(payload, requested_unit=req.unit.value)
    # Validate final payload against response model before returning (ensures schema)
    try:
        response_model = WeatherResponse.parse_obj(normalized)
    except ValidationError as exc:
        # If the external provider returns unexpected shapes, return a clean 502 with details
        return JSONResponse(status_code=502, content={"detail": "Invalid data from provider", "errors": exc.errors()})
    return response_model


@app.get("/health", name="Health Check")
async def health(check_external: bool = Query(False, description="If true, perform a quick external API probe (uses API key)"),
                 client: httpx.AsyncClient = Depends(get_client)) -> Any:
    """
    Lightweight service health endpoint.

    Returns:
    - status: "ok" when service is running
    - uptime_seconds: seconds since process start
    - version: application version
    - cache: basic cache stats (max_size, ttl_seconds, entries)
    - external_api: optional probe result (only when check_external=true)
    """
    uptime = int(time.time() - getattr(app.state, "start_time", time.time()))
    cache_stats = await _cache.stats()

    external_probe = None
    if check_external:
        # Perform a short probe to the external API. This is optional and uses a small timeout.
        try:
            probe_params = {"q": "London", "appid": settings.OPENWEATHER_API_KEY, "units": "metric"}
            resp = await client.get(settings.OPENWEATHER_API_URL, params=probe_params, timeout=2.0)
            external_probe = {"status_code": resp.status_code}
        except Exception as exc:
            external_probe = {"error": str(exc)}

    return {"status": "ok", "uptime_seconds": uptime, "version": app.version, "cache": cache_stats, "external_api": external_probe}
