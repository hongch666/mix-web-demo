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

	// ES 搜索算法脚本 (Painless)
	ES_SEARCH_SCRIPT = `
		double esScore = 1.0 / (1.0 + Math.exp(-_score));
		double score = params.esWeight * esScore;

		double aiBoost = params.aiWeight * (doc['ai_score'].size() > 0 ? doc['ai_score'].value / 10.0 : 0);

		double userBoost = params.userWeight * (doc['user_score'].size() > 0 ? doc['user_score'].value / 10.0 : 0);

		double viewsBoost = params.viewsWeight * Math.min((double)doc['views'].value / params.maxViewsNormalized, 1.0);

		double likesBoost = params.likesWeight * (doc['likeCount'].size() > 0 ? Math.min((double)doc['likeCount'].value / params.maxLikesNormalized, 1.0) : 0);

		double collectsBoost = params.collectsWeight * (doc['collectCount'].size() > 0 ? Math.min((double)doc['collectCount'].value / params.maxCollectsNormalized, 1.0) : 0);

		double followBoost = params.followWeight * (doc['authorFollowCount'].size() > 0 ? Math.min((double)doc['authorFollowCount'].value / params.maxFollowsNormalized, 1.0) : 0);

		long now = System.currentTimeMillis();
		long articleTime = doc['create_at'].value.getMillis();
		long daysDiff = (now - articleTime) / (1000L * 86400L);
		double recencyScore = Math.exp(-1.0 * (daysDiff * daysDiff) / (2.0 * params.decayDaysSq));
		double recencyBoost = params.recencyWeight * recencyScore;

		return score + aiBoost + userBoost + viewsBoost + likesBoost + collectsBoost + followBoost + recencyBoost;
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
				"user_comment_count": { "type": "integer" }
			}
		}
	}`
)
