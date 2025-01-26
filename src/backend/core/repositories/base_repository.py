from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseRepository(ABC):
    @abstractmethod
    def create(self, data: Dict) -> str:
        pass

    @abstractmethod
    def get_all(self) -> List[Dict]:
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def update(self, id: str, data: Dict) -> None:
        pass
