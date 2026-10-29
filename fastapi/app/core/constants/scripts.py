class Scripts:
    """
    脚本类 — SQL 语句、Cypher 语句、安全规则（SQL / 数据脱敏）
    """

    # ===== 增量同步 SQL 拼接 =====

    @staticmethod
    def NEO4J_SQL_INCREMENTAL_SUFFIX_FORMAT(
        base_sql: str, timestamp_column: str, sync_time_text: str
    ) -> str:
        """按时间戳列为增量同步 SQL 拼接 WHERE 与 ORDER BY 后缀"""
        return f"{base_sql} WHERE {timestamp_column} >= '{sync_time_text}' ORDER BY {timestamp_column} ASC"

    # ===== ClickHouse SQL 模板 =====

    @staticmethod
    def CACHE_VERSION_CLICKHOUSE_QUERY(table: str) -> str:
        """缓存版本号统计查询：基于表行数与最新统计时间生成版本信息"""
        return (
            "SELECT "  # noqa: S608 - 表名由内部常量传入，SQL 无法对标识符使用绑定参数
            "count() AS total_rows, "
            "ifNull(max(toUnixTimestamp(stat_time)), 0) AS max_stat_ts "
            f"FROM {table}"
        )

    # ===== Neo4j 同步 SQL =====

    NEO4J_SQL_SELECT_USERS: str = (
        "SELECT id, name, email, role, img, signature, create_at, update_at FROM user"
    )
    """增量同步使用的用户取数 SQL"""

    NEO4J_SQL_SELECT_CATEGORIES: str = "SELECT id, name, update_time FROM category"
    """增量同步使用的分类取数 SQL"""

    NEO4J_SQL_SELECT_SUB_CATEGORIES: str = (
        "SELECT id, name, category_id, update_time FROM sub_category"
    )
    """增量同步使用的子分类取数 SQL"""

    NEO4J_SQL_SELECT_ARTICLES: str = "SELECT id, title, tags, status, views, user_id, sub_category_id, create_at, update_at, content FROM articles"
    """增量同步使用的文章取数 SQL"""

    NEO4J_SQL_SELECT_LIKES: str = "SELECT user_id, article_id, created_time FROM likes"
    """增量同步使用的点赞取数 SQL"""

    NEO4J_SQL_SELECT_COLLECTS: str = (
        "SELECT user_id, article_id, created_time FROM collects"
    )
    """增量同步使用的收藏取数 SQL"""

    NEO4J_SQL_SELECT_COMMENTS: str = (
        "SELECT id, user_id, article_id, create_time, update_time FROM comments"
    )
    """增量同步使用的评论取数 SQL"""

    NEO4J_SQL_SELECT_FOCUS: str = "SELECT user_id, focus_id, created_time FROM focus"
    """增量同步使用的关注取数 SQL"""

    # ===== SQL 安全规则 =====

    SQL_QUERY_PREFIX: str = "SELECT"
    """只读查询语句的统一前缀"""

    SQL_READONLY_ALLOWED_PREFIXES: list[str] = [
        "SELECT",
        "WITH",
        "SHOW",
        "DESC",
        "DESCRIBE",
        "EXPLAIN",
    ]
    """只读语句前缀白名单"""

    SQL_DANGEROUS_KEYWORDS: list[str] = [
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
    """危险 SQL 关键字清单"""

    SQL_DANGEROUS_PATTERNS: list[str] = [
        "INTO OUTFILE",
        "INTO DUMPFILE",
        "FOR UPDATE",
        "LOCK IN SHARE MODE",
    ]
    """危险 SQL 语句正则"""

    DANGEROUS_SQL_REQUEST_PATTERNS: list[str] = [
        r"\b(update|delete|insert|drop|alter|truncate|create|replace|merge)\b",
    ]
    """识别请求文本中写库意图的正则"""

    SAFE_SQL_QUERY_REQUEST_PATTERNS: list[str] = [
        r"^(查询|查看|统计|列出|展示|获取|分析).*(最近|最新|已)?(更新|新增)的",
    ]
    """识别请求文本中只读查询意图的正则"""

    # ===== 数据脱敏规则 =====

    SANITIZER_MAX_STRING_LENGTH: int = 500
    """日志脱敏时字符串的最大长度，超出即截断"""

    SANITIZER_MAX_LIST_LENGTH: int = 10
    """日志脱敏时列表的最大长度，超出即截断"""

    SANITIZER_MAX_DICT_DEPTH: int = 5
    """日志脱敏时字典的最大递归深度"""

    SENSITIVE_KEY_PATTERNS: tuple[str, ...] = (
        "api_key",
        "apikey",
        "api-key",
        "password",
        "secret",
        "token",
        "authorization",
        "credential",
        "private_key",
        "private-key",
        "access_key",
        "access-key",
        "secret_key",
        "secret-key",
        "dsn",
        "connection_string",
        "connection-string",
    )
    """日志脱敏命中的敏感字段名模式，匹配时不区分大小写"""

    # ===== Neo4j MERGE Cypher（节点） =====

    NEO4J_MERGE_USERS_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (u:User {id: row.id})
        SET u.name = row.name, u.email = row.email, u.role = row.role,
            u.img = row.img, u.signature = row.signature,
            u.createdAt = row.createdAt, u.updatedAt = row.updatedAt
    """
    """写入用户节点及其属性的 Cypher"""
    NEO4J_MERGE_CATEGORIES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (c:Category {id: row.id}) SET c.name = row.name, c.updatedAt = row.updatedAt
    """
    """写入分类节点及其属性的 Cypher"""
    NEO4J_MERGE_SUB_CATEGORIES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (s:SubCategory {id: row.id})
        SET s.name = row.name, s.categoryId = row.categoryId, s.updatedAt = row.updatedAt
    """
    """写入子分类节点及其属性的 Cypher"""
    NEO4J_MERGE_ARTICLES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (a:Article {id: row.id})
        SET a.title = row.title, a.tags = row.tags, a.status = row.status,
            a.views = row.views, a.createAt = row.createAt, a.updateAt = row.updateAt,
            a.contentHash = row.contentHash, a.updatedAt = row.updatedAt
    """
    """写入文章节点及其属性的 Cypher"""

    # ===== Neo4j MERGE Cypher（关系） — 同步任务 _batch_write 调用 =====

    # 每条 Cypher 使用 UNWIND $rows 批量写入

    NEO4J_MERGE_TAGS_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (t:Tag {name: row.name})
    """
    """写入标签节点及其属性的 Cypher"""

    NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (s:SubCategory {id: row.subCategoryId})
        MATCH (c:Category {id: row.categoryId})
        MERGE (s)-[:BELONGS_TO]->(c)
    """
    """写入子分类归属分类关系的 Cypher"""

    NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (s:SubCategory {id: row.subCategoryId})
        MERGE (a)-[:BELONGS_TO]->(s)
    """
    """写入文章归属子分类关系的 Cypher"""

    NEO4J_MERGE_PUBLISHED_BY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (u:User {id: row.userId})
        MERGE (a)-[:PUBLISHED_BY]->(u)
    """
    """写入文章发布者关系的 Cypher"""

    NEO4J_MERGE_TAGGED_AS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MERGE (t:Tag {name: row.tagName})
        MERGE (a)-[:TAGGED_AS]->(t)
    """
    """写入文章标签关系的 Cypher"""

    NEO4J_MERGE_LIKES_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:LIKES]->(a)
        SET r.createdAt = row.createdAt
    """
    """写入点赞关系的 Cypher"""

    NEO4J_MERGE_COLLECTS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COLLECTS]->(a)
        SET r.createdAt = row.createdAt
    """
    """写入收藏关系的 Cypher"""

    NEO4J_MERGE_COMMENTED_ON_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COMMENTED_ON]->(a)
        SET r.commentId = row.commentId, r.createdAt = row.createdAt
    """
    """写入评论关系的 Cypher"""

    NEO4J_MERGE_FOLLOWS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (follower:User {id: row.followerId})
        MATCH (followed:User {id: row.followedId})
        MERGE (follower)-[r:FOLLOWS]->(followed)
        SET r.createdAt = row.createdAt
    """
    """写入关注关系的 Cypher"""

    # ===== Neo4j 精确同步删除 Cypher（按主键） =====

    NEO4J_DELETE_ARTICLES_BY_IDS_CYPHER: str = """
        UNWIND $ids AS id
        MATCH (n:Article {id: id})
        DETACH DELETE n
    """
    """按 ID 删除文章节点的 Cypher"""
    NEO4J_DELETE_USERS_BY_IDS_CYPHER: str = """
        UNWIND $ids AS id
        MATCH (n:User {id: id})
        DETACH DELETE n
    """
    """按 ID 删除用户节点的 Cypher"""
    NEO4J_DELETE_CATEGORIES_BY_IDS_CYPHER: str = """
        UNWIND $ids AS id
        MATCH (n:Category {id: id})
        DETACH DELETE n
    """
    """按 ID 删除分类节点的 Cypher"""
    NEO4J_DELETE_SUB_CATEGORIES_BY_IDS_CYPHER: str = """
        UNWIND $ids AS id
        MATCH (n:SubCategory {id: id})
        DETACH DELETE n
    """
    """按 ID 删除子分类节点的 Cypher"""
    NEO4J_DELETE_LIKES_RELATIONS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})-[r:LIKES]->(a:Article {id: row.articleId})
        DELETE r
    """
    """按 ID 删除点赞关系的 Cypher"""
    NEO4J_DELETE_COLLECTS_RELATIONS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})-[r:COLLECTS]->(a:Article {id: row.articleId})
        DELETE r
    """
    """按 ID 删除收藏关系的 Cypher"""
    NEO4J_DELETE_COMMENTED_ON_BY_IDS_CYPHER: str = """
        UNWIND $commentIds AS commentId
        MATCH (:User)-[r:COMMENTED_ON]->(:Article)
        WHERE r.commentId = commentId
        DELETE r
    """
    """按 ID 删除评论关系的 Cypher"""
    NEO4J_DELETE_FOLLOWS_RELATIONS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (follower:User {id: row.followerId})-[r:FOLLOWS]->(followed:User {id: row.followedId})
        DELETE r
    """
    """按 ID 删除关注关系的 Cypher"""

    # ===== Neo4j 清理 Cypher（同步任务 _cleanup_write 调用） =====

    # 关系清理用 keys 参数（"id1:id2" 格式的字符串列表）
    # 节点清理用 ids（整数ID列表）或 names（标签名列表）

    NEO4J_CLEANUP_PUBLISHED_BY_CYPHER: str = """
        MATCH (a:Article)-[r:PUBLISHED_BY]->(u:User)
        WITH a, r, u, toString(a.id) + ':' + toString(u.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效发布关系的 Cypher"""

    NEO4J_CLEANUP_ARTICLE_SUB_CATEGORY_CYPHER: str = """
        MATCH (a:Article)-[r:BELONGS_TO]->(s:SubCategory)
        WITH a, r, s, toString(a.id) + ':' + toString(s.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效文章与子分类关系的 Cypher"""

    NEO4J_CLEANUP_SUB_CATEGORY_CATEGORY_CYPHER: str = """
        MATCH (s:SubCategory)-[r:BELONGS_TO]->(c:Category)
        WITH s, r, c, toString(s.id) + ':' + toString(c.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效子分类与分类关系的 Cypher"""

    NEO4J_CLEANUP_TAGGED_AS_CYPHER: str = """
        MATCH (a:Article)-[r:TAGGED_AS]->(t:Tag)
        WITH a, r, t, toString(a.id) + ':' + t.name AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效文章标签关系的 Cypher"""

    NEO4J_CLEANUP_LIKES_CYPHER: str = """
        MATCH (u:User)-[r:LIKES]->(a:Article)
        WITH u, r, a, toString(u.id) + ':' + toString(a.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效点赞关系的 Cypher"""

    NEO4J_CLEANUP_COLLECTS_CYPHER: str = """
        MATCH (u:User)-[r:COLLECTS]->(a:Article)
        WITH u, r, a, toString(u.id) + ':' + toString(a.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效收藏关系的 Cypher"""

    NEO4J_CLEANUP_COMMENTED_ON_CYPHER: str = """
        MATCH (u:User)-[r:COMMENTED_ON]->(a:Article)
        WITH u, r, a, toString(r.commentId) + ':' + toString(u.id) + ':' + toString(a.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效评论关系的 Cypher"""

    NEO4J_CLEANUP_FOLLOWS_CYPHER: str = """
        MATCH (follower:User)-[r:FOLLOWS]->(followed:User)
        WITH follower, r, followed, toString(follower.id) + ':' + toString(followed.id) AS key
        WHERE NOT key IN $keys
        DELETE r
    """
    """清理失效关注关系的 Cypher"""

    NEO4J_CLEANUP_ARTICLES_CYPHER: str = """
        MATCH (n:Article)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """
    """清理失效文章节点的 Cypher"""

    NEO4J_CLEANUP_USERS_CYPHER: str = """
        MATCH (n:User)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """
    """清理失效用户节点的 Cypher"""

    NEO4J_CLEANUP_SUB_CATEGORIES_CYPHER: str = """
        MATCH (n:SubCategory)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """
    """清理失效子分类节点的 Cypher"""

    NEO4J_CLEANUP_CATEGORIES_CYPHER: str = """
        MATCH (n:Category)
        WHERE NOT n.id IN $ids
        DETACH DELETE n
    """
    """清理失效分类节点的 Cypher"""

    NEO4J_CLEANUP_TAGS_CYPHER: str = """
        MATCH (n:Tag)
        WHERE NOT n.name IN $names
        DETACH DELETE n
    """
    """清理失效标签节点的 Cypher"""

    # ===== 图谱搜索增强 Cypher（只读查询） =====

    GRAPH_SEARCH_TAG_INTEREST_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:LIKES]->(liked:Article)-[:TAGGED_AS]->(tag:Tag)
        MATCH (cand:Article)-[:TAGGED_AS]->(tag)
        WHERE cand.id IN $articleIds
        WITH cand.id AS articleId, collect(DISTINCT tag.name) AS matchedTags
        RETURN articleId, size(matchedTags) AS rawScore, matchedTags
    """
    """图谱召回查询：用户兴趣标签共现的文章"""

    GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:FOLLOWS]->(followed:User)<-[:PUBLISHED_BY]-(cand:Article)
        WHERE cand.id IN $articleIds
        WITH cand.id AS articleId, collect(DISTINCT followed.name) AS names
        RETURN articleId, names
    """
    """图谱召回查询：已关注作者的文章"""

    GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER: str = """
        MATCH (u:User {id: $userId})-[r:LIKES|COLLECTS|COMMENTED_ON]->(interacted:Article)-[:BELONGS_TO]->(sc:SubCategory)
        MATCH (cand:Article)-[:BELONGS_TO]->(sc)
        WHERE cand.id IN $articleIds
          AND NOT (u)-[:LIKES|COLLECTS|COMMENTED_ON]->(cand)
        WITH cand.id AS articleId, collect(DISTINCT sc.name) AS names
        RETURN articleId, size(names) AS rawScore, names
    """
    """图谱召回查询：同一子分类的文章"""

    GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER: str = """
        MATCH (cand:Article)-[:TAGGED_AS]->(tag:Tag)<-[:TAGGED_AS]-(other:Article)
        WHERE cand.id IN $articleIds
          AND other.id IN $articleIds
          AND other.id <> cand.id
        WITH cand.id AS articleId, collect(DISTINCT tag.name) AS names
        RETURN articleId, size(names) AS rawScore, names
    """
    """图谱召回查询：与候选文章共享标签的文章"""

    GRAPH_SEARCH_KEYWORD_TAG_CYPHER: str = """
        MATCH (cand:Article)-[:TAGGED_AS]->(tag:Tag)
        WHERE cand.id IN $articleIds AND tag.name CONTAINS $keyword
        WITH cand.id AS articleId, collect(DISTINCT tag.name) AS names
        RETURN articleId, size(names) AS rawScore, names
    """
    """图谱召回查询：关键词命中标签的文章"""

    # ===== ES 搜索排序脚本（Painless） =====

    ES_SEARCH_SCRIPT: str = """
        double esScore = 1.0 / (1.0 + Math.exp(-_score));
        double score = params.esWeight * esScore;
        double aiBoost = params.aiWeight * (doc['ai_score'].size() > 0 ? doc['ai_score'].value / 10.0 : 0);
        double userBoost = params.userWeight * (doc['user_score'].size() > 0 ? doc['user_score'].value / 10.0 : 0);
        double viewsBoost = params.viewsWeight * Math.min((double)doc['views'].value / params.maxViewsNormalized, 1.0);
        double likesBoost = params.likesWeight * (doc['like_count'].size() > 0 ? Math.min((double)doc['like_count'].value / params.maxLikesNormalized, 1.0) : 0);
        double collectsBoost = params.collectsWeight * (doc['collect_count'].size() > 0 ? Math.min((double)doc['collect_count'].value / params.maxCollectsNormalized, 1.0) : 0);
        double followBoost = params.followWeight * (doc['author_follow_count'].size() > 0 ? Math.min((double)doc['author_follow_count'].value / params.maxFollowsNormalized, 1.0) : 0);
        long now = System.currentTimeMillis();
        long articleTime = doc['create_at'].value.getMillis();
        long daysDiff = (now - articleTime) / (1000L * 86400L);
        double recencyScore = Math.exp(-1.0 * (daysDiff * daysDiff) / (2.0 * params.decayDaysSq));
        double recencyBoost = params.recencyWeight * recencyScore;
        return score + aiBoost + userBoost + viewsBoost + likesBoost + collectsBoost + followBoost + recencyBoost;
    """
    """ES 复合打分脚本（Painless），负责第一层 ES 权重计算"""

    # ===== Neo4j 意图到 Cypher 查询映射 =====

    INTENT_TO_CYPHER: dict[str, str] = {
        # 关注链（User-FOLLOWS-User-LIKES-Article）跨两跳，且 LIMIT 必须作用在展开后的文章流上；改用 OGM 只能先取出全部文章再在应用侧截断，结果集会随关注用户数放大，故保留库内 LIMIT
        "user_interest_chain": (
            "MATCH (u:User {id: $userId})-[:FOLLOWS]->(:User)-[:LIKES]->(a:Article) "
            "OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User) "
            "RETURN a.id AS id, a.title AS title, a.views AS views, author.name AS author "
            "ORDER BY a.views DESC LIMIT $limit"
        ),
        # 库内聚合统计（按标签分组计数），OGM 无法表达聚合
        "tag_graph": (
            "MATCH (t:Tag)<-[:TAGGED_AS]-(a:Article) "
            "RETURN t.name AS tag, count(a) AS articleCount "
            "ORDER BY articleCount DESC LIMIT $limit"
        ),
        # 多跳聚合：按共同标签分组计数、排除已互动文章并按相关度排序，且需 `collect(DISTINCT t.name)` 聚集标签，OGM 无法表达
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
    """意图类型到图谱查询名的映射"""
