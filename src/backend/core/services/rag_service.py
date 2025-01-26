from typing import Optional
from pathlib import Path
import httpx

from llama_index.core import (
    VectorStoreIndex,
    Settings,
    Document,
    StorageContext,
)
from llama_index.core.base.base_query_engine import BaseQueryEngine

from src.backend.core.services.llm_service import LLMService
from src.backend.core.services.vector_store_service import VectorStoreService
from src.backend.core.services.file_processor import FileProcessor
from src.backend.core.services.query_engine_service import QueryEngineService

class RAGService:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.llm_service = LLMService()
        self.vector_store_service = VectorStoreService()
        self.query_engine_service = QueryEngineService()
        self.current_file_id: Optional[str] = None
        
        Settings.embed_model = self.llm_service.embedding_model

    def process_file(self, file_path: str | Path, file_id: str) -> VectorStoreIndex:
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        documents = self.file_processor.read_file(file_path)
        if not documents:
            raise ValueError("No documents were processed")
        
        vector_store = self.vector_store_service.get_or_create_collection(file_id, recreate=True)
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
            
        vector_store = self.vector_store_service.get_collection(file_id)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
        )
        
        Settings.llm = self.llm_service.get_llm_for_query(question)
        
        try:
            query_engine = self.query_engine_service.create(index)
            response = query_engine.query(question)
            
            if not response or not str(response).strip():
                return "I couldn't find relevant information to answer your question. Could you please rephrase or ask something else?"
                
            return str(response)
            
        except httpx.ReadTimeout:
            return "I apologize, but the response took too long to generate. This might happen with very complex questions. Could you try asking a simpler question or breaking it down into parts?"
        except Exception as e:
            return f"An error occurred while processing your question: {str(e)}"
