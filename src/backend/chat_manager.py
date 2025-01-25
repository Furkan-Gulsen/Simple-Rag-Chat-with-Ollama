from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid
from datetime import datetime

from pymongo import MongoClient
from src.backend.rag_engine import RAGEngine

@dataclass
class Message:
    role: str
    content: str
    avatar: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "avatar": self.avatar,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            role=data["role"],
            content=data["content"],
            avatar=data.get("avatar"),
            timestamp=data.get("timestamp", datetime.utcnow())
        )

class SessionRepository:
    def __init__(self, db):
        self.sessions = db.sessions
        
    def create(self, filename: str, file_path: str) -> str:
        session_id = str(uuid.uuid4())
        session_doc = {
            "session_id": session_id,
            "filename": filename,
            "file_path": file_path,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "message_count": 0
        }
        self.sessions.insert_one(session_doc)
        return session_id

    def get_all(self) -> List[Dict]:
        return list(self.sessions.find({}, {"_id": 0}).sort("last_accessed", -1))

    def get_by_id(self, session_id: str) -> Optional[Dict]:
        return self.sessions.find_one({"session_id": session_id}, {"_id": 0})

    def update_access(self, session_id: str):
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"last_accessed": datetime.utcnow()},
                "$inc": {"message_count": 1}
            }
        )

class ChatRepository:
    def __init__(self, db):
        self.chats = db.chats

    def save(self, session_id: str, question: str, answer: str):
        chat_doc = {
            "session_id": session_id,
            "messages": [
                Message("user", question).to_dict(),
                Message("assistant", answer).to_dict()
            ]
        }
        self.chats.insert_one(chat_doc)

    def get_history(self, session_id: str) -> List[Dict]:
        chat_docs = self.chats.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("messages.timestamp", 1)
        
        messages = []
        for doc in chat_docs:
            messages.extend(doc["messages"])
        return messages

class ChatSession:
    def __init__(self, session_id: str, chat_repo: ChatRepository, session_repo: SessionRepository):
        self.session_id = session_id
        self.chat_repo = chat_repo
        self.session_repo = session_repo
        self.messages: List[Message] = []
        self._load_history()

    def _load_history(self):
        messages_data = self.chat_repo.get_history(self.session_id)
        self.messages = [Message.from_dict(msg) for msg in messages_data]

    def add_message(self, role: str, content: str, avatar: Optional[str] = None):
        message = Message(role, content, avatar)
        self.messages.append(message)
        self.chat_repo.save(self.session_id, content, "")
        self.session_repo.update_access(self.session_id)

class ChatManager:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        db = MongoClient(mongo_uri).rag_chat_db
        self.session_repo = SessionRepository(db)
        self.chat_repo = ChatRepository(db)
        self.rag_engine = RAGEngine()
        self.current_session: Optional[ChatSession] = None

    def create_session(self, filename: str, file_path: str) -> str:
        session_id = self.session_repo.create(filename, file_path)
        self.rag_engine.process_file(file_path, session_id)
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
        answer = self.rag_engine.query(session_id, question)
        self.chat_repo.save(session_id, question, answer)
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