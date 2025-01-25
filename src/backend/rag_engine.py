from typing import List, Optional, Protocol
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    Settings,
    Document,
    StorageContext,
)
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
import httpx

from src.utils.config import (
    OLLAMA_HOST,
    MISTRAL_MODEL,
    CODE_MODEL
)
from src.backend.file_processor import FileProcessor

class LLMProvider:
    def __init__(self, host: str, timeout: float = 300.0):
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

class VectorStoreManager:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)

    def get_or_create_collection(self, file_id: str, recreate: bool = False) -> ChromaVectorStore:
        collection_name = f"file_{file_id}"
        
        if recreate:
            try:
                self.client.delete_collection(collection_name)
            except ValueError:
                pass
                
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"file_id": file_id}
        )
        
        return ChromaVectorStore(chroma_collection=collection)

    def get_collection(self, file_id: str) -> ChromaVectorStore:
        collection_name = f"file_{file_id}"
        try:
            collection = self.client.get_collection(collection_name)
            return ChromaVectorStore(chroma_collection=collection)
        except ValueError:
            raise ValueError("No index available for this file. Please process the file first.")

class QueryEngineFactory:
    @staticmethod
    def create(index: VectorStoreIndex) -> BaseQueryEngine:
        return index.as_query_engine(
            similarity_top_k=5,
            response_mode="tree_summarize",
        )

class RAGEngine:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.llm_provider = LLMProvider(OLLAMA_HOST)
        self.vector_store_manager = VectorStoreManager()
        self.current_file_id: Optional[str] = None
        
        Settings.embed_model = self.llm_provider.embedding_model

    def process_file(self, file_path: str | Path, file_id: str) -> VectorStoreIndex:
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        documents = self.file_processor.read_file(file_path)
        if not documents:
            raise ValueError("No documents were processed")
        
        vector_store = self.vector_store_manager.get_or_create_collection(file_id, recreate=True)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        self.current_file_id = file_id
        return index

    def query(self, file_id: str, question: str) -> str:
        if not file_id:
            raise ValueError("No file ID provided")
            
        vector_store = self.vector_store_manager.get_collection(file_id)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
        )
        
        Settings.llm = self.llm_provider.get_llm_for_query(question)
        
        try:
            query_engine = QueryEngineFactory.create(index)
            response = query_engine.query(question)
            
            if not response or not str(response).strip():
                return "I couldn't find relevant information to answer your question. Could you please rephrase or ask something else?"
                
            return str(response)
            
        except httpx.ReadTimeout:
            return "I apologize, but the response took too long to generate. This might happen with very complex questions. Could you try asking a simpler question or breaking it down into parts?"
        except Exception as e:
            return f"An error occurred while processing your question: {str(e)}" 