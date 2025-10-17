from typing import List, Dict, Any
from sqlmodel import Session, text
from functools import lru_cache
from common.utils import fileLogger as logger
from config import load_config
class VectorMapper:
    
    def __init__(self):
        self.topK = load_config("embedding").get("top_k", 5) if load_config("embedding") else 5

    def search_similar_articles(
        self, 
        pg_db: Session, 
        query_embedding: List[float], 
        limit: int | None
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索"""
        if limit is None:
            limit = self.topK  # 运行时再使用实例属性
        try:
            # 将向量转为字符串格式 '[0.1, 0.2, ...]'
            query_vector_str = str(query_embedding)
            
            query = text("""
                SELECT 
                    article_id,
                    title,
                    content_preview,
                    1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
                FROM article_vector
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:query_vector AS vector)
                LIMIT :limit
            """)
            
            result = pg_db.execute(
                query,
                {
                    "query_vector": query_vector_str, 
                    "limit": limit
                }
            )
            
            articles = []
            for row in result:
                articles.append({
                    "article_id": row.article_id,
                    "title": row.title,
                    "content_preview": row.content_preview,
                    "similarity": float(row.similarity)
                })
            
            return articles
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def upsert_article_vector(
        self, 
        pg_db: Session, 
        article_id: int, 
        title: str,
        content_preview: str,
        embedding: List[float]
    ):
        """插入或更新文章向量"""
        try:
            # 将向量列表转换为字符串格式 [0.1, 0.2, ...]
            embedding_str = str(embedding)
            
            query = text("""
                INSERT INTO article_vector (article_id, title, content_preview, embedding)
                VALUES (:article_id, :title, :content_preview, CAST(:embedding AS vector))
                ON CONFLICT (article_id) 
                DO UPDATE SET 
                    title = EXCLUDED.title,
                    content_preview = EXCLUDED.content_preview,
                    embedding = EXCLUDED.embedding,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            pg_db.execute(query, {
                "article_id": article_id,
                "title": title,
                "content_preview": content_preview,
                "embedding": embedding_str
            })
            pg_db.commit()
        except Exception as e:
            logger.error(f"更新文章向量失败: {e}")
            pg_db.rollback()
    
    def delete_article_vector(self, pg_db: Session, article_id: int):
        """删除文章向量"""
        try:
            query = text("DELETE FROM article_vector WHERE article_id = :article_id")
            pg_db.execute(query, {"article_id": article_id})
            pg_db.commit()
        except Exception as e:
            logger.error(f"删除文章向量失败: {e}")
            pg_db.rollback()
    
    def get_existing_articles_hash(self, pg_db: Session) -> Dict[int, str]:
        """获取已存在文章的内容哈希值（用于快速对比是否需要更新）"""
        try:
            query = text("""
                SELECT article_id, title, content_preview
                FROM article_vector
            """)
            result = pg_db.execute(query)
            
            # 返回 {article_id: "title|content_preview"}
            hash_dict = {}
            for row in result:
                # 简单拼接作为内容标识
                content_key = f"{row.title}|{row.content_preview}"
                hash_dict[row.article_id] = content_key
            
            return hash_dict
        except Exception as e:
            logger.error(f"获取已存在文章哈希失败: {e}")
            return {}
    
    def get_articles_need_sync(
        self, 
        mysql_db: Session, 
        pg_db: Session,
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """获取需要同步的文章（MySQL 中有但 PG 中没有或已更新的）"""
        try:
            # 获取 MySQL 中的文章
            mysql_query = text("""
                SELECT id, title, content, update_at
                FROM article
                ORDER BY update_at DESC
                LIMIT :batch_size
            """)
            mysql_articles = mysql_db.execute(mysql_query, {"batch_size": batch_size}).fetchall()
            
            # 获取 PG 中已有的文章
            pg_query = text("""
                SELECT article_id, updated_at
                FROM article_vector
            """)
            pg_articles = {
                row.article_id: row.updated_at 
                for row in pg_db.execute(pg_query).fetchall()
            }
            
            # 找出需要同步的文章
            need_sync = []
            for article in mysql_articles:
                article_id = article.id
                mysql_update_time = article.update_at
                
                # 如果 PG 中没有，或者 MySQL 更新时间更晚
                if (article_id not in pg_articles or 
                    mysql_update_time > pg_articles[article_id]):
                    need_sync.append({
                        "id": article_id,
                        "title": article.title,
                        "content": article.content[:500]  # 只取前500字
                    })
            
            return need_sync
        except Exception as e:
            logger.error(f"获取待同步文章失败: {e}")
            return []
    
    def sync_deleted_articles(self, mysql_db: Session, pg_db: Session) -> int:
        """同步已删除的文章（从向量表中删除在 MySQL 中不存在的文章）"""
        try:
            # 获取 PG 中的所有 article_id
            pg_query = text("SELECT article_id FROM article_vector")
            pg_article_ids = {row.article_id for row in pg_db.execute(pg_query).fetchall()}
            
            # 获取 MySQL 中的所有 article_id
            mysql_query = text("SELECT id FROM articles")
            mysql_article_ids = {row.id for row in mysql_db.execute(mysql_query).fetchall()}
            
            # 找出需要删除的文章（在 PG 但不在 MySQL）
            deleted_ids = pg_article_ids - mysql_article_ids
            
            delete_count = 0
            for article_id in deleted_ids:
                self.delete_article_vector(pg_db, article_id)
                delete_count += 1
            
            if delete_count > 0:
                logger.info(f"同步删除了 {delete_count} 篇文章")
            
            return delete_count
        except Exception as e:
            logger.error(f"同步删除文章失败: {e}")
            return 0

@lru_cache()
def get_vector_mapper() -> VectorMapper:
    return VectorMapper()