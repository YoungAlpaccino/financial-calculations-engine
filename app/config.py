"""
Settings (sketch).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "financial-calculations-engine-sketch"
    db_url:   str = "postgresql://user:pass@localhost:5432/calc_engine"
    debug:    bool = False
    host:     str = "0.0.0.0"
    port:     int = 8080

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
