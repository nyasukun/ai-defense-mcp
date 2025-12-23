
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AIC_MANAGEMENT_API_KEY = os.getenv("AIC_MANAGEMENT_API_KEY")
    AIC_MANAGEMENT_API_URL = os.getenv("AIC_MANAGEMENT_API_URL", "https://api.security.cisco.com/api/ai-defense/v1")

    @classmethod
    def validate(cls):
        if not cls.AIC_MANAGEMENT_API_KEY:
            raise ValueError("AIC_MANAGEMENT_API_KEY environment variable is required")
