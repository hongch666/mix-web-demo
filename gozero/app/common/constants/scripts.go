package constants

// ===== 脚本类 — SQL DDL/查询、ES 搜索脚本、ES 索引 Mapping、Lua 脚本 =====

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
			conversation_low bigint GENERATED ALWAYS AS (LEAST(sender_id, receiver_id)) VIRTUAL COMMENT '会话对端较小ID',
			conversation_high bigint GENERATED ALWAYS AS (GREATEST(sender_id, receiver_id)) VIRTUAL COMMENT '会话对端较大ID',
			PRIMARY KEY (id),
			KEY idx_conversation_created (conversation_low, conversation_high, created_at, id),
			KEY idx_receiver_unread (receiver_id, is_read, sender_id),
			KEY idx_receiver_sender_read (receiver_id, sender_id, is_read)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`

	// ES_ARTICLES_INDEX_NAME 文章检索使用的 ES 索引名
	ES_ARTICLES_INDEX_NAME = "articles"

	// 分布式锁解锁 Lua 脚本：只有当锁的值与传入标识一致时才删除，保证只有锁持有者才能解锁
	UNLOCK_LUA_SCRIPT = `
if redis.call("get", KEYS[1]) == ARGV[1] then
	return redis.call("del", KEYS[1])
else
	return 0
end
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
				"tags": {
					"type": "text",
					"analyzer": "ik_smart",
					"search_analyzer": "ik_smart",
					"fields": {
						"keyword": { "type": "keyword", "ignore_above": 256 }
					}
				},
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
