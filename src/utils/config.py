from pathlib import Path
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()

def get_project_paths():
    root_dir = Path(__file__).parent.parent.parent
    data_dir = root_dir / "data"
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return root_dir, data_dir, uploads_dir

@dataclass
class PathConfig:
    root_dir: Path = field(default_factory=lambda: get_project_paths()[0])
    data_dir: Path = field(default_factory=lambda: get_project_paths()[1])
    uploads_dir: Path = field(default_factory=lambda: get_project_paths()[2])

@dataclass
class OllamaConfig:
    host: str = "http://localhost:11434"
    mistral_model: str = "mistral"
    code_model: str = "codellama"

@dataclass
class FileConfig:
    supported_types: List[str] = field(default_factory=lambda: ["txt", "pdf", "doc", "docx"])


@dataclass
class AppConfig:
    paths: PathConfig = field(default_factory=PathConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    files: FileConfig = field(default_factory=FileConfig)

config = AppConfig()

OLLAMA_HOST = config.ollama.host
MISTRAL_MODEL = config.ollama.mistral_model
CODE_MODEL = config.ollama.code_model
SUPPORTED_FILE_TYPES = config.files.supported_types
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
