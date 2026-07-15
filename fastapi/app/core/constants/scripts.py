"""
脚本类 — SQL 语句、Cypher 语句、SQL 安全规则
"""
from typing import List


class Scripts:
    # ===== SQL 建表 =====
    AI_CHAT_SQL_TABLE_EXISTENCE_CHECK: str = (
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ai_history'"
    )
    AI_CHAT_SQL_TABLE_CREATION_MESSAGE: str = """
        CREATE TABLE `ai_history` (
            `id` BIGINT NOT NULL AUTO_INCREMENT,
            `user_id` BIGINT,
            `ask` TEXT NOT NULL,
            `reply` TEXT NOT NULL,
            `thinking` TEXT,
            `ai_type` VARCHAR(30),
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            KEY `idx_user_id` (`user_id`)
        ) COMMENT='AI聊天记录' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """

    # ===== Neo4j 同步 SQL =====
    NEO4J_SQL_SELECT_USERS: str = "SELECT id, name, email, role, img, signature, create_at, update_at FROM user"
    NEO4J_SQL_SELECT_CATEGORIES: str = "SELECT id, name, update_time FROM category"
    NEO4J_SQL_SELECT_SUB_CATEGORIES: str = "SELECT id, name, category_id, update_time FROM sub_category"
    NEO4J_SQL_SELECT_ARTICLES: str = "SELECT id, title, tags, status, views, user_id, sub_category_id, create_at, update_at, content FROM articles"
    NEO4J_SQL_SELECT_LIKES: str = "SELECT user_id, article_id, created_time FROM likes"
    NEO4J_SQL_SELECT_COLLECTS: str = "SELECT user_id, article_id, created_time FROM collects"
    NEO4J_SQL_SELECT_COMMENTS: str = "SELECT id, user_id, article_id, create_time, update_time FROM comments"
    NEO4J_SQL_SELECT_FOCUS: str = "SELECT user_id, focus_id, created_time FROM focus"
    NEO4J_SQL_INCREMENTAL_SUFFIX_FORMAT: str = "%s WHERE %s >= '%s' ORDER BY %s ASC"

    # ===== SQL 安全规则 =====
    SQL_QUERY_PREFIX: str = "SELECT"
    SQL_READONLY_ALLOWED_PREFIXES: List[str] = ["SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"]
    SQL_DANGEROUS_KEYWORDS: List[str] = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
        "REPLACE", "MERGE", "CALL", "GRANT", "REVOKE", "COMMIT", "ROLLBACK",
        "SET", "USE", "RENAME", "LOCK", "UNLOCK", "HANDLER", "LOAD",
        "ANALYZE", "OPTIMIZE", "REPAIR", "KILL",
    ]
    SQL_DANGEROUS_PATTERNS: List[str] = ["INTO OUTFILE", "INTO DUMPFILE", "FOR UPDATE", "LOCK IN SHARE MODE"]
    DANGEROUS_SQL_REQUEST_PATTERNS: List[str] = [
        r"\b(update|delete|insert|drop|alter|truncate|create|replace|merge)\b",
    ]
    SAFE_SQL_QUERY_REQUEST_PATTERNS: List[str] = [
        r"^(查询|查看|统计|列出|展示|获取|分析).*(最近|最新|已)?(更新|新增)的",
    ]

    # ===== Neo4j 约束 =====
    NEO4J_CREATE_CONSTRAINTS: List[str] = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT sub_category_id_unique IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
    ]

    # ===== Neo4j MERGE Cypher =====
    NEO4J_MERGE_USERS_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (u:User {id: row.id})
        SET u.name = row.name, u.email = row.email, u.role = row.role,
            u.img = row.img, u.signature = row.signature,
            u.createdAt = row.createdAt, u.updatedAt = row.updatedAt
    """
    NEO4J_MERGE_CATEGORIES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (c:Category {id: row.id}) SET c.name = row.name, c.updatedAt = row.updatedAt
    """
    NEO4J_MERGE_SUB_CATEGORIES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (s:SubCategory {id: row.id})
        SET s.name = row.name, s.categoryId = row.categoryId, s.updatedAt = row.updatedAt
    """
    NEO4J_MERGE_ARTICLES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (a:Article {id: row.id})
        SET a.title = row.title, a.tags = row.tags, a.status = row.status,
            a.views = row.views, a.createAt = row.createAt, a.updateAt = row.updateAt,
            a.contentHash = row.contentHash, a.updatedAt = row.updatedAt
    """
