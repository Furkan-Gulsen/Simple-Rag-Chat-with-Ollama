from typing import List, Dict, Optional
from pymongo.database import Database
from src.backend.core.entities.message import Message
from src.backend.core.repositories.base_repository import BaseRepository

class ChatRepository(BaseRepository):
    def __init__(self, db: Database):
        self.chats = db.chats

    def create(self, data: Dict) -> str:
        chat_doc = {
            "session_id": data["session_id"],
            "messages": [
                Message("user", data["question"]).to_dict(),
                Message("assistant", data["answer"]).to_dict()
            ]
        }
        result = self.chats.insert_one(chat_doc)
        return str(result.inserted_id)

    def get_all(self) -> List[Dict]:
        return list(self.chats.find({}, {"_id": 0}))

    def get_by_id(self, id: str) -> Optional[Dict]:
        return self.chats.find_one({"_id": id}, {"_id": 0})

    def update(self, id: str, data: Dict) -> None:
        self.chats.update_one(
            {"_id": id},
            {"$set": data}
        )

    def get_history(self, session_id: str) -> List[Dict]:
        chat_docs = self.chats.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("messages.timestamp", 1)
        
        messages = []
        for doc in chat_docs:
            messages.extend(doc["messages"])
        return messages
