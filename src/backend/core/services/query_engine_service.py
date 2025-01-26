from llama_index.core import VectorStoreIndex
from llama_index.core.base.base_query_engine import BaseQueryEngine

class QueryEngineService:
    def create(self, index: VectorStoreIndex) -> BaseQueryEngine:
        return index.as_query_engine(
            similarity_top_k=5,
            response_mode="tree_summarize",
        )
