from typing import List, Optional
from src.backend.core.entities.message import Message
from src.backend.core.repositories.chat_repository import ChatRepository
from src.backend.core.repositories.session_repository import SessionRepository

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
        self.chat_repo.create({
            "session_id": self.session_id,
            "question": content,
            "answer": ""
        })
        self.session_repo.update_access(self.session_id)
