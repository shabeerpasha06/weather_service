from typing import Dict, Optional

from pydantic import BaseModel, Field, StrictStr, conint, confloat
from enum import Enum


class TemperatureUnit(str, Enum):
    centigrade = "centigrade"
    fahrenheit = "fahrenheit"
    kelvin = "kelvin"


class CityWeatherRequest(BaseModel):
    city: StrictStr = Field(..., min_length=1, max_length=100, description="City name")
    unit: TemperatureUnit = Field(..., description="temperature unit")

    class Config:
        anystr_strip_whitespace = True


class WeatherMain(BaseModel):
    temp: confloat(strict=True)
    feels_like: confloat(strict=True)
    temp_min: confloat(strict=True)
    temp_max: confloat(strict=True)
    pressure: conint(strict=True)
    humidity: conint(strict=True)


class WeatherWind(BaseModel):
    speed: confloat(strict=True)
    deg: Optional[conint(strict=True)] = None


class WeatherSys(BaseModel):
    country: Optional[StrictStr] = None
    sunrise: Optional[int] = None
    sunset: Optional[int] = None


class WeatherResponse(BaseModel):
    city: StrictStr
    country: Optional[StrictStr] = None
    unit: TemperatureUnit
    weather: Dict[str, str] = Field(..., description="Short weather info from provider")
    main: WeatherMain
    wind: Optional[WeatherWind] = None
    sys: Optional[WeatherSys] = None
    raw: Optional[Dict] = Field(
        None, description="Raw JSON returned by external provider (kept optional)"
    )
