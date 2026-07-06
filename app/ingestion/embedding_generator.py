from google import genai
from google.genai import types
from chromadb import EmbeddingFunction, Documents, Embeddings
from app.core.config import settings
from app.core.logger import logger


class EmbeddingGenerator:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            cls._client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized.")
        return cls._client

    @classmethod
    def get_embeddings(cls, texts) -> list:
        client = cls.get_client()
        logger.info(f"Generating embeddings for {len(texts)} documents")
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        embeddings = [list(e.values) for e in response.embeddings]
        logger.info(f"Received {len(embeddings)} embeddings, dim={len(embeddings[0])}")
        return embeddings


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        logger.info(f"GeminiEmbeddingFunction called with {len(input)} documents")
        return EmbeddingGenerator.get_embeddings(list(input))