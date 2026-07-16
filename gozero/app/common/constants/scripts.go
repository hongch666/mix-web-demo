package constants

// 脚本类 — SQL DDL/查询、ES 搜索脚本、ES 索引 Mapping
const (
	// chat_messages 建表 SQL
	CREATE_CHAT_MESSAGES_TABLE_SQL = `
		CREATE TABLE IF NOT EXISTS chat_messages (
			id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
			sender_id varchar(50) NOT NULL COMMENT '发送者ID',
			receiver_id varchar(50) NOT NULL COMMENT '接收者ID',
			content text NOT NULL COMMENT '消息内容',
			is_read tinyint NOT NULL DEFAULT 0 COMMENT '是否已读，0未读，1已读',
			created_at datetime(3) DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
			PRIMARY KEY (id),
			KEY idx_sender_receiver (sender_id, receiver_id)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`

	// comments 联表评分查询
	COMMENT_RATING_QUERY = `
		SELECT
			c.article_id,
			CASE WHEN u.role = 'ai' THEN 'ai' ELSE 'user' END as role_type,
			AVG(c.star) as avg_star,
			COUNT(*) as comment_count
		FROM comments c
		LEFT JOIN user u ON c.user_id = u.id
		WHERE c.article_id IN (?) AND c.star > 0
		GROUP BY c.article_id, role_type
	`

	// ES 搜索算法脚本 (Painless, 全量13项)
	ES_SEARCH_SCRIPT = `
		double esScore = 1.0 / (1.0 + Math.exp(-_score));
		double total = params.esWeight * esScore;

		total += params.aiWeight * (doc['ai_score'].size() > 0 ? doc['ai_score'].value / 10.0 : 0);
		total += params.userWeight * (doc['user_score'].size() > 0 ? doc['user_score'].value / 10.0 : 0);
		total += params.viewsWeight * Math.min((double)doc['views'].value / params.maxViewsNormalized, 1.0);
		total += params.likesWeight * (doc['likeCount'].size() > 0 ? Math.min((double)doc['likeCount'].value / params.maxLikesNormalized, 1.0) : 0);
		total += params.collectsWeight * (doc['collectCount'].size() > 0 ? Math.min((double)doc['collectCount'].value / params.maxCollectsNormalized, 1.0) : 0);
		total += params.followWeight * (doc['authorFollowCount'].size() > 0 ? Math.min((double)doc['authorFollowCount'].value / params.maxFollowsNormalized, 1.0) : 0);

		long now = System.currentTimeMillis();
		long articleTime = doc['create_at'].value.getMillis();
		long daysDiff = (now - articleTime) / (1000L * 86400L);
		double recencyScore = Math.exp(-1.0 * (daysDiff * daysDiff) / (2.0 * params.decayDaysSq));
		total += params.recencyWeight * recencyScore;

		if (params.queryVector != null && doc['embedding_vector'].size() == 1024) {
			double vecSim = Math.max(0.0, cosineSimilarity(params.queryVector, 'embedding_vector'));
			total += params.vectorWeight * vecSim;
		}

		if (params.userTagList != null && params.userTagList.length > 0 && !doc['tag_list'].empty) {
			double interestMatch = 0.0;
			for (tag in doc['tag_list']) {
				for (ut in params.userTagList) { if (tag.equals(ut)) { interestMatch += 1.0; } }
			}
			total += params.graphInterestWeight * Math.min(interestMatch / 5.0, 1.0);
		}

		if (params.followedAuthorIds != null && params.followedAuthorIds.length > 0) {
			for (fid in params.followedAuthorIds) { if (fid == doc['userId'].value) { total += params.graphFollowWeight; break; } }
		}

		if (params.preferredSubCatIds != null && params.preferredSubCatIds.length > 0) {
			for (sid in params.preferredSubCatIds) { if (sid == doc['sub_category_id'].value) { total += params.graphSubcatWeight; break; } }
		}

		if (params.keywordTags != null && params.keywordTags.length > 0 && !doc['tag_list'].empty) {
			double kwTagMatch = 0.0;
			for (tag in doc['tag_list']) { for (kt in params.keywordTags) { if (tag.contains(kt)) { kwTagMatch += 1.0; break; } } }
			total += params.graphKeywordWeight * Math.min(kwTagMatch / 3.0, 1.0);
		}

		return total;
	`

	// ES 传统8项子分脚本 (script_fields 用)
	ES_TRAD_SCORE_SCRIPT = `
		double esScore = 1.0 / (1.0 + Math.exp(-_score));
		double total = params.esWeight * esScore;
		total += params.aiWeight * (doc['ai_score'].size() > 0 ? doc['ai_score'].value / 10.0 : 0);
		total += params.userWeight * (doc['user_score'].size() > 0 ? doc['user_score'].value / 10.0 : 0);
		total += params.viewsWeight * Math.min((double)doc['views'].value / params.maxViewsNormalized, 1.0);
		total += params.likesWeight * (doc['likeCount'].size() > 0 ? Math.min((double)doc['likeCount'].value / params.maxLikesNormalized, 1.0) : 0);
		total += params.collectsWeight * (doc['collectCount'].size() > 0 ? Math.min((double)doc['collectCount'].value / params.maxCollectsNormalized, 1.0) : 0);
		total += params.followWeight * (doc['authorFollowCount'].size() > 0 ? Math.min((double)doc['authorFollowCount'].value / params.maxFollowsNormalized, 1.0) : 0);
		long now = System.currentTimeMillis();
		long articleTime = doc['create_at'].value.getMillis();
		long daysDiff = (now - articleTime) / (1000L * 86400L);
		double recencyScore = Math.exp(-1.0 * (daysDiff * daysDiff) / (2.0 * params.decayDaysSq));
		total += params.recencyWeight * recencyScore;
		return total;
	`

	// ES 向量子分脚本
	ES_VEC_SCORE_SCRIPT = `
		if (params.qv != null && doc['embedding_vector'].size() == 1024) {
			return Math.max(0.0, cosineSimilarity(params.qv, 'embedding_vector'));
		}
		return 0.0;
	`

	// ES 图谱子分脚本
	ES_GRAPH_SCORE_SCRIPT = `
		double total = 0.0;
		if (params.utl != null && params.utl.length > 0 && !doc['tag_list'].empty) {
			double m = 0.0;
			for (tag in doc['tag_list']) { for (ut in params.utl) { if (tag.equals(ut)) { m += 1.0; } } }
			total += params.giw * Math.min(m / 5.0, 1.0);
		}
		if (params.fai != null && params.fai.length > 0) {
			for (fid in params.fai) { if (fid == doc['userId'].value) { total += params.gfw; break; } }
		}
		if (params.psi != null && params.psi.length > 0) {
			for (sid in params.psi) { if (sid == doc['sub_category_id'].value) { total += params.gsw; break; } }
		}
		if (params.kwt != null && params.kwt.length > 0 && !doc['tag_list'].empty) {
			double km = 0.0;
			for (tag in doc['tag_list']) { for (kt in params.kwt) { if (tag.contains(kt)) { km += 1.0; break; } } }
			total += params.gkw * Math.min(km / 3.0, 1.0);
		}
		return Math.min(total, 1.0);
	`

	// ES 索引 Mapping 定义
	ES_INDEX_MAPPING = `{
		"mappings": {
			"properties": {
				"id": { "type": "integer" },
				"title": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"content": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"userId": { "type": "integer" },
				"username": { "type": "keyword" },
				"category_name": { "type": "keyword" },
				"sub_category_name": { "type": "keyword" },
				"tags": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"status": { "type": "integer" },
				"views": { "type": "integer" },
				"likeCount": { "type": "integer" },
				"collectCount": { "type": "integer" },
				"authorFollowCount": { "type": "integer" },
				"create_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"update_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"ai_score": { "type": "float" },
				"user_score": { "type": "float" },
				"ai_comment_count": { "type": "integer" },
				"user_comment_count": { "type": "integer" },
				"tag_list": { "type": "keyword" },
				"sub_category_id": { "type": "integer" },
				"embedding_vector": { "type": "dense_vector", "dims": 1024 }
			}
		}
	}`

	// pgvector: 读取文章全部 chunk 向量
	PGVECTOR_AVERAGE_CHUNKS_QUERY = `
		SELECT embedding FROM langchain_pg_embedding
		WHERE cmetadata->>'article_id' = $1
	`

	// Neo4j: 查询活跃用户
	NEO4J_ACTIVE_USERS_CYPHER = `
		MATCH (u:User)
		WHERE exists((u)-[:LIKES|COLLECTS|COMMENTED_ON|FOLLOWS|PUBLISHED_BY]->())
		RETURN DISTINCT u.id AS id
	`

	// Neo4j: 用户兴趣标签
	NEO4J_USER_TAG_INTEREST_CYPHER = `
		MATCH (u:User {id: $uid})-[:LIKES|COLLECTS]->(a:Article)-[:TAGGED_AS]->(t:Tag)
		RETURN collect(DISTINCT t.name) AS tags
	`

	// Neo4j: 用户关注作者
	NEO4J_USER_FOLLOWED_AUTHORS_CYPHER = `
		MATCH (u:User {id: $uid})-[:FOLLOWS]->(f:User)
		RETURN collect(DISTINCT f.id) AS ids
	`

	// Neo4j: 用户常看子分类
	NEO4J_USER_PREFERRED_SUBCAT_CYPHER = `
		MATCH (u:User {id: $uid})-[:LIKES|COLLECTS|COMMENTED_ON]->(a:Article)
		-[:BELONGS_TO]->(sc:SubCategory)
		RETURN collect(DISTINCT sc.id) AS ids
	`
)
