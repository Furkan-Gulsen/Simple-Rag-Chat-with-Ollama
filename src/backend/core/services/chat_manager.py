from typing import List, Dict, Optional, Any
from pymongo import MongoClient
from src.backend.core.services.chat_session import ChatSession
from src.backend.core.repositories.chat_repository import ChatRepository
from src.backend.core.repositories.session_repository import SessionRepository
from src.backend.core.services.rag_service import RAGService

class ChatManager:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        db = MongoClient(mongo_uri).rag_chat_db
        self.session_repo = SessionRepository(db)
        self.chat_repo = ChatRepository(db)
        self.rag_service = RAGService()
        self.current_session: Optional[ChatSession] = None

    def create_session(self, filename: str, file_path: str) -> str:
        session_id = self.session_repo.create({
            "filename": filename,
            "file_path": file_path
        })
        self.rag_service.process_file(file_path, session_id)
        self.current_session = ChatSession(session_id, self.chat_repo, self.session_repo)
        return session_id

    def load_session(self, session_id: str) -> bool:
        if not self.session_repo.get_by_id(session_id):
            return False
        self.current_session = ChatSession(session_id, self.chat_repo, self.session_repo)
        return True

    def get_all_sessions(self) -> List[Dict]:
        return self.session_repo.get_all()

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.session_repo.get_by_id(session_id)

    def get_chat_history_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        return self.chat_repo.get_history(session_id)

    def query(self, session_id: str, question: str) -> str:
        if not self.session_repo.get_by_id(session_id):
            raise ValueError("Invalid session ID")
        answer = self.rag_service.query(session_id, question)
        self.chat_repo.create({
            "session_id": session_id,
            "question": question,
            "answer": answer
        })
        self.session_repo.update_access(session_id)
        return answer

    def get_response(self, user_message: str) -> str:
        if not self.current_session:
            raise ValueError("No active session")
        
        self.current_session.add_message("user", user_message, "🧑‍💻")
        
        try:
            response = self.query(self.current_session.session_id, user_message)
            self.current_session.add_message("assistant", response, "🤖")
            return response
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            self.current_session.add_message("assistant", error_message, "⚠️")
            return error_message
