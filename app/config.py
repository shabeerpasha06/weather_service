from typing import Literal, Mapping

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    OPENWEATHER_API_KEY: str = Field(..., env="OPENWEATHER_API_KEY")
    OPENWEATHER_API_URL: str = Field(
        "https://api.openweathermap.org/data/2.5/weather", env="OPENWEATHER_API_URL"
    )
    CACHE_MAX_SIZE: int = Field(100, env="CACHE_MAX_SIZE", ge=1, le=1000)
    CACHE_TTL_SECONDS: int = Field(300, env="CACHE_TTL_SECONDS", ge=1, le=86400)

    UnitCentigrade: Literal["centigrade"] = "centigrade"
    UnitFahrenheit: Literal["fahrenheit"] = "fahrenheit"
    UnitKelvin: Literal["kelvin"] = "kelvin"

    UNIT_MAPPING: Mapping[str, str] = {
        "centigrade": "metric",
        "fahrenheit": "imperial",
        "kelvin": "standard",
    }

    @validator("OPENWEATHER_API_KEY")
    def ensure_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("OPENWEATHER_API_KEY must be set")
        return v.strip()

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
