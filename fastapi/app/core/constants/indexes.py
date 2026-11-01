class MySQLIndexes:
    """MySQL 索引补齐定义，元素为 (表名, 索引名, 索引列定义)

    MySQL 不支持 CREATE INDEX IF NOT EXISTS，初始化时先查 information_schema.statistics，
    缺失才执行 ALTER TABLE，因此这里只声明期望存在的索引，可重复执行
    """

    AI_HISTORY: tuple[tuple[str, str, str], ...] = (
        ("ai_history", "idx_user_created", "(user_id, created_at, id)"),
        ("ai_history", "idx_user_id_id", "(user_id, id)"),
    )
    """按用户读取上下文、按用户清理历史的覆盖索引"""

    ALL: tuple[tuple[str, str, str], ...] = AI_HISTORY
    """需要在启动时补齐的全部 MySQL 索引"""


class PostgreSQLIndexes:
    """pgvector 向量表索引定义，表由 LangChain PGVector 在首次写入时创建"""

    EXTENSION: str = "CREATE EXTENSION IF NOT EXISTS vector"
    """pgvector 扩展，索引使用 vector 类型前必须先启用"""

    EMBEDDING_TABLE: str = "langchain_pg_embedding"
    """LangChain PGVector 默认向量表名"""

    HNSW: str = (
        "CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_hnsw "
        "ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops)"
    )
    """向量近邻索引，检索按余弦距离（<=>）排序时命中"""

    IVFFLAT: str = (
        "CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_ivfflat "
        "ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    """HNSW 不可用（pgvector < 0.5）时的降级索引"""

    ARTICLE_ID: str = (
        "CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_article_id "
        "ON langchain_pg_embedding (collection_id, ((cmetadata ->> 'article_id')))"
    )
    """按文章 ID 查删向量的表达式索引，避免全表扫描 jsonb"""


class ClickHouseIndexes:
    """ClickHouse 跳数索引与 TTL 定义，通过 ALTER ... IF NOT EXISTS 幂等补齐"""

    DATA_SKIPPING: tuple[tuple[str, str, str, str], ...] = (
        ("dwd_user_action", "idx_action_type", "action_type", "set(64)"),
        ("dwd_user_action", "idx_user_id", "user_id", "minmax"),
        ("dwd_user_action", "idx_article_id", "article_id", "minmax"),
        ("dwd_api_call", "idx_api_path", "api_path", "bloom_filter(0.01)"),
        ("ods_article_log", "idx_action", "action", "set(64)"),
        ("ods_article_log", "idx_created_at", "created_at", "minmax"),
        ("ods_api_log", "idx_created_at", "created_at", "minmax"),
    )
    """按查询过滤列补建跳数索引，排序键保持 event_id 以维持 ReplacingMergeTree 去重"""

    TTL: tuple[tuple[str, str], ...] = (
        ("ods_api_log", "created_at + INTERVAL 24 MONTH"),
        ("ods_article_log", "created_at + INTERVAL 24 MONTH"),
        ("dwd_api_call", "action_date + INTERVAL 24 MONTH"),
        ("dwd_user_action", "action_date + INTERVAL 24 MONTH"),
    )
    """日志类事件表保留 24 个月，表必须按月分区才能按分区淘汰"""
