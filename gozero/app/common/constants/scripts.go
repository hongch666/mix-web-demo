package constants

// ===== 脚本类 — SQL DDL/查询、ES 搜索脚本、ES 索引 Mapping =====

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
			KEY idx_sender_receiver (sender_id, receiver_id),
			KEY idx_receiver_unread (receiver_id, is_read, sender_id),
			KEY idx_sender_receiver_created (sender_id, receiver_id, created_at),
			KEY idx_receiver_sender_created (receiver_id, sender_id, created_at)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`

	// ES_ARTICLES_INDEX_NAME 文章检索使用的 ES 索引名
	ES_ARTICLES_INDEX_NAME = "articles"

	// INDEX_EXISTS_SQL 检查索引是否已存在，MySQL 没有 CREATE INDEX IF NOT EXISTS，只能先查后建
	INDEX_EXISTS_SQL = `
		SELECT 1 FROM information_schema.statistics
		WHERE table_schema = DATABASE() AND table_name = ? AND index_name = ?
		LIMIT 1
	`

	// ES 索引 Mapping 定义
	// settings 必须与 mapping 同时下发：索引建成后分片数与副本数无法修改
	// id 用 long 对应 Go 侧 int64，username 用 lowercase normalizer 让前缀匹配与大小写解耦
	ES_INDEX_MAPPING = `{
		"settings": {
			"number_of_shards": 1,
			"number_of_replicas": 0,
			"analysis": {
				"normalizer": {
					"lowercase_normalizer": {
						"type": "custom",
						"filter": ["lowercase"]
					}
				}
			}
		},
		"mappings": {
			"properties": {
				"id": { "type": "long" },
				"title": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"content": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"user_id": { "type": "long" },
				"username": { "type": "keyword", "normalizer": "lowercase_normalizer" },
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

// MySQLIndexDefinition 描述一条需要补齐的 MySQL 索引
type MySQLIndexDefinition struct {
	// Table 目标表名
	Table string
	// Name 索引名
	Name string
	// Columns 索引列定义，含括号
	Columns string
}

// CHAT_MESSAGES_INDEXES 启动期需要补齐的 chat_messages 索引
// 与 db/mysql/gozero/chat_messages.sql 以及建表 SQL 中的索引保持一致
var CHAT_MESSAGES_INDEXES = []MySQLIndexDefinition{
	{Table: "chat_messages", Name: "idx_receiver_unread", Columns: "(receiver_id, is_read, sender_id)"},
	{Table: "chat_messages", Name: "idx_sender_receiver_created", Columns: "(sender_id, receiver_id, created_at)"},
	{Table: "chat_messages", Name: "idx_receiver_sender_created", Columns: "(receiver_id, sender_id, created_at)"},
}
