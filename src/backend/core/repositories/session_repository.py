from datetime import datetime
import uuid
from typing import List, Dict, Optional
from pymongo.database import Database
from src.backend.core.repositories.base_repository import BaseRepository

class SessionRepository(BaseRepository):
    def __init__(self, db: Database):
        self.sessions = db.sessions
        
    def create(self, data: Dict) -> str:
        session_id = str(uuid.uuid4())
        session_doc = {
            "session_id": session_id,
            "filename": data["filename"],
            "file_path": data["file_path"],
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "message_count": 0
        }
        self.sessions.insert_one(session_doc)
        return session_id

    def get_all(self) -> List[Dict]:
        return list(self.sessions.find({}, {"_id": 0}).sort("last_accessed", -1))

    def get_by_id(self, id: str) -> Optional[Dict]:
        return self.sessions.find_one({"session_id": id}, {"_id": 0})

    def update(self, id: str, data: Dict) -> None:
        self.sessions.update_one(
            {"session_id": id},
            {"$set": data}
        )

    def update_access(self, session_id: str) -> None:
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"last_accessed": datetime.utcnow()},
                "$inc": {"message_count": 1}
            }
        )
