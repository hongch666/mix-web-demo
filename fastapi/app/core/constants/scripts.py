from typing import Dict, List, Tuple


class Scripts:
    """
    脚本类 — SQL 语句、Cypher 语句、安全规则（SQL / 数据脱敏）
    """

    # ===== SQL 建表 =====
    AI_CHAT_SQL_TABLE_EXISTENCE_CHECK: str = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ai_history'"
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
    NEO4J_SQL_SELECT_USERS: str = (
        "SELECT id, name, email, role, img, signature, create_at, update_at FROM user"
    )
    NEO4J_SQL_SELECT_CATEGORIES: str = "SELECT id, name, update_time FROM category"
    NEO4J_SQL_SELECT_SUB_CATEGORIES: str = (
        "SELECT id, name, category_id, update_time FROM sub_category"
    )
    NEO4J_SQL_SELECT_ARTICLES: str = "SELECT id, title, tags, status, views, user_id, sub_category_id, create_at, update_at, content FROM articles"
    NEO4J_SQL_SELECT_LIKES: str = "SELECT user_id, article_id, created_time FROM likes"
    NEO4J_SQL_SELECT_COLLECTS: str = (
        "SELECT user_id, article_id, created_time FROM collects"
    )
    NEO4J_SQL_SELECT_COMMENTS: str = (
        "SELECT id, user_id, article_id, create_time, update_time FROM comments"
    )
    NEO4J_SQL_SELECT_FOCUS: str = "SELECT user_id, focus_id, created_time FROM focus"
    NEO4J_SQL_INCREMENTAL_SUFFIX_FORMAT: str = "%s WHERE %s >= '%s' ORDER BY %s ASC"

    # ===== SQL 安全规则 =====
    SQL_QUERY_PREFIX: str = "SELECT"
    SQL_READONLY_ALLOWED_PREFIXES: List[str] = [
        "SELECT",
        "WITH",
        "SHOW",
        "DESC",
        "DESCRIBE",
        "EXPLAIN",
    ]
    SQL_DANGEROUS_KEYWORDS: List[str] = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
        "MERGE",
        "CALL",
        "GRANT",
        "REVOKE",
        "COMMIT",
        "ROLLBACK",
        "SET",
        "USE",
        "RENAME",
        "LOCK",
        "UNLOCK",
        "HANDLER",
        "LOAD",
        "ANALYZE",
        "OPTIMIZE",
        "REPAIR",
        "KILL",
    ]
    SQL_DANGEROUS_PATTERNS: List[str] = [
        "INTO OUTFILE",
        "INTO DUMPFILE",
        "FOR UPDATE",
        "LOCK IN SHARE MODE",
    ]
    DANGEROUS_SQL_REQUEST_PATTERNS: List[str] = [
        r"\b(update|delete|insert|drop|alter|truncate|create|replace|merge)\b",
    ]
    SAFE_SQL_QUERY_REQUEST_PATTERNS: List[str] = [
        r"^(查询|查看|统计|列出|展示|获取|分析).*(最近|最新|已)?(更新|新增)的",
    ]

    # ===== 数据脱敏规则 =====
    SANITIZER_MAX_STRING_LENGTH: int = 500  # 字符串最大长度（超出截断）
    SANITIZER_MAX_LIST_LENGTH: int = 10  # 列表最大长度（超出截断）
    SANITIZER_MAX_DICT_DEPTH: int = 5  # 字典最大递归深度

    # 敏感字段键名模式（不区分大小写匹配）
    SENSITIVE_KEY_PATTERNS: Tuple[str, ...] = (
        "api_key", "apikey", "api-key", "password", "secret", "token",
        "authorization", "credential", "private_key", "private-key",
        "access_key", "access-key", "secret_key", "secret-key",
        "dsn", "connection_string", "connection-string",
    )

    # ===== Neo4j 约束 =====
    NEO4J_CREATE_CONSTRAINTS: List[str] = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT sub_category_id_unique IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
    ]

    # ===== Neo4j MERGE Cypher（节点） =====
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

    # ===== Neo4j MERGE Cypher（关系） — 同步任务 _batch_write 调用 =====
    # 每条 Cypher 使用 UNWIND $rows 批量写入

    # Tag 节点
    NEO4J_MERGE_TAGS_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (t:Tag {name: row.name})
    """

    # SubCategory -[:BELONGS_TO]-> Category
    NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (s:SubCategory {id: row.subCategoryId})
        MATCH (c:Category {id: row.categoryId})
        MERGE (s)-[:BELONGS_TO]->(c)
    """

    # Article -[:BELONGS_TO]-> SubCategory
    NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (s:SubCategory {id: row.subCategoryId})
        MERGE (a)-[:BELONGS_TO]->(s)
    """

    # Article -[:PUBLISHED_BY]-> User
    NEO4J_MERGE_PUBLISHED_BY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (u:User {id: row.userId})
        MERGE (a)-[:PUBLISHED_BY]->(u)
    """

    # Article -[:TAGGED_AS]-> Tag
    NEO4J_MERGE_TAGGED_AS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MERGE (t:Tag {name: row.tagName})
        MERGE (a)-[:TAGGED_AS]->(t)
    """

    # User -[:LIKES]-> Article（含创建时间）
    NEO4J_MERGE_LIKES_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:LIKES]->(a)
        SET r.createdAt = row.createdAt
    """

    # User -[:COLLECTS]-> Article（含创建时间）
    NEO4J_MERGE_COLLECTS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COLLECTS]->(a)
        SET r.createdAt = row.createdAt
    """

    # User -[:COMMENTED_ON]-> Article（含评论ID和创建时间）
    NEO4J_MERGE_COMMENTED_ON_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COMMENTED_ON]->(a)
        SET r.commentId = row.commentId, r.createdAt = row.createdAt
    """

    # User -[:FOLLOWS]-> User（含创建时间）
    NEO4J_MERGE_FOLLOWS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (follower:User {id: row.followerId})
        MATCH (followed:User {id: row.followedId})
        MERGE (follower)-[r:FOLLOWS]->(followed)
        SET r.createdAt = row.createdAt
    """

    # ===== Neo4j 清理 Cypher（同步任务 _cleanup_write 调用） =====
    # 关系清理用 keys 参数（"id1:id2" 格式的字符串列表）
    # 节点清理用 ids（整数ID列表）或 names（标签名列表）

    # 清理 PUBLISHED_BY 关系
    NEO4J_CLEANUP_PUBLISHED_BY_CYPHER: str = """
        MATCH (a:Article)-[r:PUBLISHED_BY]->(u:User)
        WITH a, r, u, toString(a.id) + ':' + toString(u.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 Article -[:BELONGS_TO]-> SubCategory 关系
    NEO4J_CLEANUP_ARTICLE_SUB_CATEGORY_CYPHER: str = """
        MATCH (a:Article)-[r:BELONGS_TO]->(s:SubCategory)
        WITH a, r, s, toString(a.id) + ':' + toString(s.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 SubCategory -[:BELONGS_TO]-> Category 关系
    NEO4J_CLEANUP_SUB_CATEGORY_CATEGORY_CYPHER: str = """
        MATCH (s:SubCategory)-[r:BELONGS_TO]->(c:Category)
        WITH s, r, c, toString(s.id) + ':' + toString(c.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 Article -[:TAGGED_AS]-> Tag 关系
    NEO4J_CLEANUP_TAGGED_AS_CYPHER: str = """
        MATCH (a:Article)-[r:TAGGED_AS]->(t:Tag)
        WITH a, r, t, toString(a.id) + ':' + t.name AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 User -[:LIKES]-> Article 关系
    NEO4J_CLEANUP_LIKES_CYPHER: str = """
        MATCH (u:User)-[r:LIKES]->(a:Article)
        WITH u, r, a, toString(u.id) + ':' + toString(a.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 User -[:COLLECTS]-> Article 关系
    NEO4J_CLEANUP_COLLECTS_CYPHER: str = """
        MATCH (u:User)-[r:COLLECTS]->(a:Article)
        WITH u, r, a, toString(u.id) + ':' + toString(a.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 User -[:COMMENTED_ON]-> Article 关系（key 格式: commentId:userId:articleId）
    NEO4J_CLEANUP_COMMENTED_ON_CYPHER: str = """
        MATCH (u:User)-[r:COMMENTED_ON]->(a:Article)
        WITH u, r, a, toString(r.commentId) + ':' + toString(u.id) + ':' + toString(a.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理 User -[:FOLLOWS]-> User 关系
    NEO4J_CLEANUP_FOLLOWS_CYPHER: str = """
        MATCH (follower:User)-[r:FOLLOWS]->(followed:User)
        WITH follower, r, followed, toString(follower.id) + ':' + toString(followed.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """

    # 清理不在 ids 中的 Article 节点（级联删除关联关系）
    NEO4J_CLEANUP_ARTICLES_CYPHER: str = """
        MATCH (n:Article)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """

    # 清理不在 ids 中的 User 节点（级联删除关联关系）
    NEO4J_CLEANUP_USERS_CYPHER: str = """
        MATCH (n:User)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """

    # 清理不在 ids 中的 SubCategory 节点（级联删除关联关系）
    NEO4J_CLEANUP_SUB_CATEGORIES_CYPHER: str = """
        MATCH (n:SubCategory)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """

    # 清理不在 ids 中的 Category 节点（级联删除关联关系）
    NEO4J_CLEANUP_CATEGORIES_CYPHER: str = """
        MATCH (n:Category)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """

    # 清理不在 names 列表中的 Tag 节点（级联删除关联关系）
    NEO4J_CLEANUP_TAGS_CYPHER: str = """
        MATCH (n:Tag)
        WHERE NOT n.name IN $names
        DETACH DELETE n
    """

    # ===== 图谱搜索增强 Cypher（只读查询） =====

    # 信号1：用户兴趣标签 — 候选文章与用户点赞文章共享的标签数
    # 路径: User-LIKES-Article-TAGGED_AS-Tag
    # 入参: userId, articleIds  /  返回: articleId, rawScore, matchedTags
    GRAPH_SEARCH_TAG_INTEREST_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:LIKES]->(liked:Article)-[:TAGGED_AS]->(tag:Tag)
        MATCH (cand:Article)-[:TAGGED_AS]->(tag)
        WHERE cand.id IN $articleIds
        WITH cand.id AS articleId, collect(DISTINCT tag.name) AS matchedTags
        RETURN articleId, size(matchedTags) AS rawScore, matchedTags
    """

    # 信号2：关注作者 — 候选文章作者是否在用户关注列表里
    # 路径: User-FOLLOWS-User-PUBLISHED_BY-Article
    # 入参: userId, articleIds  /  返回: articleId, names
    GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:FOLLOWS]->(followed:User)<-[:PUBLISHED_BY]-(cand:Article)
        WHERE cand.id IN $articleIds
        WITH cand.id AS articleId, collect(DISTINCT followed.name) AS names
        RETURN articleId, names
    """

    # 信号3：同子分类 — 候选文章是否属于用户近期互动过的子分类
    # 路径: User-LIKES|COLLECTS|COMMENTED_ON-Article-BELONGS_TO-SubCategory
    # 入参: userId, articleIds  /  返回: articleId, rawScore, names
    GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER: str = """
        MATCH (u:User {id: $userId})-[r:LIKES|COLLECTS|COMMENTED_ON]->(interacted:Article)-[:BELONGS_TO]->(sc:SubCategory)
        MATCH (cand:Article)-[:BELONGS_TO]->(sc)
        WHERE cand.id IN $articleIds
          AND NOT (u)-[:LIKES|COLLECTS|COMMENTED_ON]->(cand)
        WITH cand.id AS articleId, collect(DISTINCT sc.name) AS names
        RETURN articleId, size(names) AS rawScore, names
    """

    # 信号4：候选间相似标签 — 候选文章两两之间共享的标签数
    # 路径: Article-TAGGED_AS-Tag-TAGGED_AS-Article
    # 入参: articleIds  /  返回: articleId, rawScore, names
    GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER: str = """
        MATCH (cand:Article)-[:TAGGED_AS]->(tag:Tag)<-[:TAGGED_AS]-(other:Article)
        WHERE cand.id IN $articleIds
          AND other.id IN $articleIds
          AND other.id <> cand.id
        WITH cand.id AS articleId, collect(DISTINCT tag.name) AS names
        RETURN articleId, size(names) AS rawScore, names
    """

    # 信号5：关键词标签命中 — 候选文章中包含关键词相关标签的文章
    # 路径: Article-TAGGED_AS-Tag
    # 入参: articleIds, keyword  /  返回: articleId, rawScore, names
    GRAPH_SEARCH_KEYWORD_TAG_CYPHER: str = """
        MATCH (cand:Article)-[:TAGGED_AS]->(tag:Tag)
        WHERE cand.id IN $articleIds AND tag.name CONTAINS $keyword
        WITH cand.id AS articleId, collect(DISTINCT tag.name) AS names
        RETURN articleId, size(names) AS rawScore, names
    """

    # ===== Neo4j 意图到 Cypher 查询映射 =====
    # 预定义查询，Agent 通过 query_name 参数调用
    INTENT_TO_CYPHER: Dict[str, str] = {
        "article_detail": (
            "MATCH (a:Article {id: $id}) "
            "OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(u:User) "
            "OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:SubCategory) "
            "OPTIONAL MATCH (s)-[:BELONGS_TO_CATEGORY]->(c:Category) "
            "OPTIONAL MATCH (a)-[:TAGGED_AS]->(t:Tag) "
            "RETURN a.id AS id, a.title AS title, a.views AS views, "
            "u.name AS author, s.name AS subCategory, c.name AS category, "
            "collect(DISTINCT t.name) AS tags"
        ),
        "category_articles": (
            "MATCH (s:SubCategory {name: $name})<-[:BELONGS_TO]-(a:Article) "
            "OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(u:User) "
            "RETURN a.id AS id, a.title AS title, a.views AS views, "
            "a.createAt AS createAt, u.name AS author "
            "ORDER BY a.views DESC LIMIT $limit"
        ),
        "user_articles": (
            "MATCH (a:Article)-[:PUBLISHED_BY]->(u:User {name: $name}) "
            "RETURN a.id AS id, a.title AS title, a.views AS views, a.createAt AS createAt "
            "ORDER BY a.createAt DESC LIMIT $limit"
        ),
        "similar_articles_same_category": (
            "MATCH (a:Article {id: $articleId})-[:BELONGS_TO]->(s:SubCategory) "
            "MATCH (other:Article)-[:BELONGS_TO]->(s) "
            "WHERE other.id <> a.id "
            "OPTIONAL MATCH (other)-[:PUBLISHED_BY]->(u:User) "
            "RETURN other.id AS id, other.title AS title, other.views AS views, "
            "u.name AS author "
            "ORDER BY other.views DESC LIMIT $limit"
        ),
        "user_interest_chain": (
            "MATCH (u:User {id: $userId})-[:FOLLOWS]->(:User)-[:LIKES]->(a:Article) "
            "OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User) "
            "RETURN a.id AS id, a.title AS title, a.views AS views, author.name AS author "
            "ORDER BY a.views DESC LIMIT $limit"
        ),
        "top_viewed_articles": (
            "MATCH (a:Article) "
            "RETURN a.id AS id, a.title AS title, a.views AS views "
            "ORDER BY a.views DESC LIMIT $limit"
        ),
        "tag_graph": (
            "MATCH (t:Tag)<-[:TAGGED_AS]-(a:Article) "
            "RETURN t.name AS tag, count(a) AS articleCount "
            "ORDER BY articleCount DESC LIMIT $limit"
        ),
        "user_recommendation": (
            "MATCH (u:User {id: $userId})-[:LIKES|COLLECTS]->(interest:Article) "
            "MATCH (interest)-[:TAGGED_AS]->(t:Tag) "
            "MATCH (a:Article)-[:TAGGED_AS]->(t) "
            "WHERE a.id <> interest.id "
            "AND NOT EXISTS { (u)-[:LIKES|COLLECTS]->(a) } "
            "OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User) "
            "WITH a, author, t "
            "RETURN a.id AS id, a.title AS title, author.name AS author, "
            "collect(DISTINCT t.name) AS matchTags, "
            "count(DISTINCT t) AS relevance "
            "ORDER BY relevance DESC, a.views DESC LIMIT $limit"
        ),
    }
