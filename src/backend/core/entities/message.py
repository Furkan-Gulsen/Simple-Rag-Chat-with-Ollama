from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

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
