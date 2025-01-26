from pathlib import Path
from typing import List
from llama_index.core import Document
from llama_index.readers.file import PDFReader, DocxReader
from llama_index.core.node_parser import SimpleNodeParser

from src.utils.config import CHUNK_SIZE, CHUNK_OVERLAP

class BaseFileReader:
    def can_handle(self, file_extension: str) -> bool:
        raise NotImplementedError
        
    def read(self, file_path: Path) -> List[Document]:
        raise NotImplementedError

class PDFFileReader(BaseFileReader):
    def __init__(self):
        self.reader = PDFReader()
        
    def can_handle(self, file_extension: str) -> bool:
        return file_extension == '.pdf'
        
    def read(self, file_path: Path) -> List[Document]:
        return self.reader.load_data(file_path)

class DocxFileReader(BaseFileReader):
    def __init__(self):
        self.reader = DocxReader()
        
    def can_handle(self, file_extension: str) -> bool:
        return file_extension in ['.doc', '.docx']
        
    def read(self, file_path: Path) -> List[Document]:
        return self.reader.load_data(file_path)

class TextFileReader(BaseFileReader):
    def can_handle(self, file_extension: str) -> bool:
        return True
        
    def read(self, file_path: Path) -> List[Document]:
        return [Document(text=file_path.read_text())]

class DocumentProcessor:
    def __init__(self):
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
    
    def process(self, documents: List[Document]) -> List[Document]:
        return documents

class FileProcessor:
    def __init__(self):
        self.readers = [
            PDFFileReader(),
            DocxFileReader(),
            TextFileReader()
        ]
        self.document_processor = DocumentProcessor()
    
    def validate_file(self, file_path: Path) -> bool:
        return file_path.suffix.lower().replace('.', '') in SUPPORTED_FILE_TYPES
    
    def read_file(self, file_path: str | Path) -> List[Document]:
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        for reader in self.readers:
            if reader.can_handle(extension):
                documents = reader.read(file_path)
                return self.document_processor.process(documents)
                
        raise ValueError(f"Unsupported file type: {extension}")
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        return documents
