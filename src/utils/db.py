from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

from pymongo import MongoClient
from bson import ObjectId

@dataclass
class FileSession:
    file_name: str
    created_at: datetime
    id: Optional[str] = None

@dataclass
class ChatMessage:
    file_id: str
    messages: List[Dict[str, Any]]
    updated_at: datetime

class FileRepository(Protocol):
    def create(self, file_session: FileSession) -> str:
        pass
        
    def get_all(self) -> List[FileSession]:
        pass
        
    def delete(self, file_id: str) -> bool:
        pass

class ChatRepository(Protocol):
    def save(self, chat_message: ChatMessage) -> None:
        pass
        
    def get_history(self, file_id: str) -> List[Dict[str, Any]]:
        pass
        
    def delete(self, file_id: str) -> bool:
        pass

class MongoFileRepository:
    def __init__(self, collection):
        self.collection = collection

    def create(self, file_session: FileSession) -> str:
        file_data = {
            "file_name": file_session.file_name,
            "created_at": file_session.created_at
        }
        result = self.collection.insert_one(file_data)
        return str(result.inserted_id)

    def get_all(self) -> List[FileSession]:
        files = self.collection.find()
        return [
            FileSession(
                id=str(f["_id"]),
                file_name=f["file_name"],
                created_at=f["created_at"]
            )
            for f in files
        ]

    def delete(self, file_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(file_id)})
        return result.deleted_count > 0

class MongoChatRepository:
    def __init__(self, collection):
        self.collection = collection

    def save(self, chat_message: ChatMessage) -> None:
        chat_data = {
            "file_id": chat_message.file_id,
            "messages": chat_message.messages,
            "updated_at": chat_message.updated_at
        }
        
        self.collection.update_one(
            {"file_id": chat_message.file_id},
            {"$set": chat_data},
            upsert=True
        )

    def get_history(self, file_id: str) -> List[Dict[str, Any]]:
        chat = self.collection.find_one({"file_id": file_id})
        return chat["messages"] if chat else []

    def delete(self, file_id: str) -> bool:
        result = self.collection.delete_one({"file_id": file_id})
        return result.deleted_count > 0

class DatabaseManager:
    def __init__(self, host: str = "localhost", port: int = 27017):
        client = MongoClient(host, port)
        db = client.rag_chat_db
        
        self.file_repo = MongoFileRepository(db.files)
        self.chat_repo = MongoChatRepository(db.chats)

    def create_file_session(self, file_name: str) -> str:
        file_session = FileSession(
            file_name=file_name,
            created_at=datetime.utcnow()
        )
        return self.file_repo.create(file_session)

    def get_file_sessions(self) -> List[FileSession]:
        return self.file_repo.get_all()

    def save_chat(self, file_id: str, messages: List[Dict[str, Any]]) -> None:
        chat_message = ChatMessage(
            file_id=file_id,
            messages=messages,
            updated_at=datetime.utcnow()
        )
        self.chat_repo.save(chat_message)

    def get_chat_history(self, file_id: str) -> List[Dict[str, Any]]:
        return self.chat_repo.get_history(file_id)

    def delete_file_session(self, file_id: str) -> bool:
        chat_deleted = self.chat_repo.delete(file_id)
        file_deleted = self.file_repo.delete(file_id)
        return file_deleted 