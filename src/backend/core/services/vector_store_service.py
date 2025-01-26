import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

class VectorStoreService:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)

    def get_or_create_collection(self, file_id: str, recreate: bool = False) -> ChromaVectorStore:
        collection_name = f"file_{file_id}"
        
        if recreate:
            try:
                self.client.delete_collection(collection_name)
            except ValueError:
                pass
                
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"file_id": file_id}
        )
        
        return ChromaVectorStore(chroma_collection=collection)

    def get_collection(self, file_id: str) -> ChromaVectorStore:
        collection_name = f"file_{file_id}"
        try:
            collection = self.client.get_collection(collection_name)
            return ChromaVectorStore(chroma_collection=collection)
        except ValueError:
            raise ValueError("No index available for this file. Please process the file first.")
