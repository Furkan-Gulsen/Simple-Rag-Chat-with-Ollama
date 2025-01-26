from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from src.utils.config import (
    OLLAMA_HOST,
    MISTRAL_MODEL,
    CODE_MODEL
)

class LLMService:
    def __init__(self, host: str = OLLAMA_HOST, timeout: float = 300.0):
        self.chat_llm = Ollama(
            model=MISTRAL_MODEL,
            temperature=0.7,
            base_url=host,
            request_timeout=timeout,
        )
        self.code_llm = Ollama(
            model=CODE_MODEL,
            temperature=0.2,
            base_url=host,
            request_timeout=timeout,
        )
        self.embedding_model = OllamaEmbedding(
            model_name=MISTRAL_MODEL,
            base_url=host,
            request_timeout=timeout,
        )

    def get_llm_for_query(self, query: str):
        code_terms = ["code", "function", "class", "programming", "syntax"]
        return self.code_llm if any(term in query.lower() for term in code_terms) else self.chat_llm
