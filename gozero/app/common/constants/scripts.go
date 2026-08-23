package constants

// 脚本类 — SQL DDL/查询、ES 搜索脚本、ES 索引 Mapping
const (
	// chat_messages 建表 SQL
	CREATE_CHAT_MESSAGES_TABLE_SQL = `
		CREATE TABLE IF NOT EXISTS chat_messages (
			id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
			sender_id bigint NOT NULL COMMENT '发送者ID',
			receiver_id bigint NOT NULL COMMENT '接收者ID',
			content text NOT NULL COMMENT '消息内容',
			is_read tinyint NOT NULL DEFAULT 0 COMMENT '是否已读，0未读，1已读',
			created_at datetime(3) DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
			PRIMARY KEY (id),
			KEY idx_sender_receiver (sender_id, receiver_id)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`

	// ES 索引 Mapping 定义
	ES_INDEX_MAPPING = `{
		"mappings": {
			"properties": {
				"id": { "type": "integer" },
				"title": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"content": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"user_id": { "type": "integer" },
				"username": { "type": "keyword" },
				"category_name": { "type": "keyword" },
				"sub_category_name": { "type": "keyword" },
				"tags": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"status": { "type": "integer" },
				"views": { "type": "integer" },
				"like_count": { "type": "integer" },
				"collect_count": { "type": "integer" },
				"author_follow_count": { "type": "integer" },
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
