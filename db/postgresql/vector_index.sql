-- ============================================================
-- pgvector 向量表索引（LangChain PGVector 默认表名）
-- 表由应用首次写入时自动创建，需在表存在后执行本脚本
-- ============================================================

-- 向量近邻索引：检索 SQL 为 ORDER BY embedding <=> query LIMIT k，只对余弦距离生效
-- pgvector >= 0.5 用 HNSW；更低版本改用下方注释里的 IVFFlat
CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_hnsw
    ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops);

-- 降级方案（pgvector < 0.5）：建索引前先 ANALYZE langchain_pg_embedding
-- CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_ivfflat
--     ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 按文章 ID 查删向量的表达式索引：对应 cmetadata ->> 'article_id'
CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_article_id
    ON langchain_pg_embedding (collection_id, ((cmetadata ->> 'article_id')));
