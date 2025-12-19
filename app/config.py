import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", 8080))
    AUTH_MODE: str = os.getenv("AUTH_MODE", "none").lower()
    AUTH_TOKEN: str = os.getenv("AUTH_TOKEN", "")
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET: str = os.getenv("OAUTH_CLIENT_SECRET", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "") # For weather tool
    REQUEST_LOG_FILE: str = os.getenv("REQUEST_LOG_FILE", "requests.log")  # Full request logging

settings = Settings()

