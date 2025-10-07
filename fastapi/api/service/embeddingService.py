from functools import lru_cache
from typing import List
from sentence_transformers import SentenceTransformer
from common.utils import fileLogger as logger
from config import load_config

class EmbeddingService:
    def __init__(self):
        try:
            embedding_config = load_config("embedding") or {}
            self.model = SentenceTransformer(embedding_config.get("model", 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
            self.dimension = embedding_config.get("dimension", 384)
            logger.info("Embedding 模型加载成功")
        except Exception as e:
            logger.error(f"加载 Embedding 模型失败: {e}")
            self.model = None
    
    def encode_text(self, text: str) -> List[float]:
        """将文本转换为向量"""
        if not self.model:
            return [0.0] * self.dimension
        try:
            text = text[:512]  # 截断
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            return [0.0] * self.dimension
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        if not self.model:
            return [[0.0] * self.dimension] * len(texts)
        try:
            texts = [t[:512] for t in texts]
            embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"批量向量化失败: {e}")
            return [[0.0] * self.dimension] * len(texts)

@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()