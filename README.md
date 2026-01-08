# FastAPI Weather Service

Simple FastAPI microservice to fetch weather data for a given city and temperature unit.

Features
- Pydantic request/response models validate and enforce schema.
- Async calls to OpenWeatherMap using a single httpx AsyncClient for connection reuse.
- Small TTL LRU in-memory cache to reduce external calls while bounding memory usage.
- Clear error handling and typed responses.

Environment variables
- OPENWEATHER_API_KEY (required): your OpenWeatherMap API key.
- OPENWEATHER_API_URL (optional): override the external API URL (default is OpenWeatherMap).
- CACHE_MAX_SIZE (optional): maximum number of cached entries (default 100).
- CACHE_TTL_SECONDS (optional): cache TTL in seconds (default 300).

Run locally
1. Create a virtualenv and install requirements:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set env var:
   ```
   export OPENWEATHER_API_KEY="your_api_key_here"
   ```

3. Start the app:
   ```
   uvicorn app.main:app --reload
   ```

Example request
```
curl -X POST "http://127.0.0.1:8000/weather" \
  -H "Content-Type: application/json" \
  -d '{"city":"Bangalore","unit":"centigrade"}'
```
