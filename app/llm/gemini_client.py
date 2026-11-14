from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logger import logger


class GeminiClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            api_key = settings.GEMINI_API_KEY.strip()
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            cls._client = genai.Client(api_key=api_key)
            logger.info("Gemini text client initialized.")
        return cls._client

    @classmethod
    def generate_response(
        cls,
        prompt: str,
        system_instruction: str = None,
        model_name: str = "gemini-2.5-flash"
    ) -> str:
        client = cls.get_client()
        config = types.GenerateContentConfig(
            temperature=0.1,
            system_instruction=system_instruction
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        if not response.text or not response.text.strip():
            raise RuntimeError("Gemini returned an empty response.")
        return response.text