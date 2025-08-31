package migrate

import (
	"fmt"

	"gin_proj/common/utils"
	"gin_proj/config"
	"gin_proj/entity/po"
)

// InitMigrate 检查并按需创建表（仅在表不存在时执行 CREATE TABLE DDL）
func InitMigrate() {
	if config.DB == nil {
		utils.FileLogger.Info("config.DB 为 nil，跳过表迁移/创建")
		return
	}

	migrator := config.DB.Migrator()
	// 可用模型检查表是否存在
	if migrator.HasTable(&po.ChatMessage{}) || migrator.HasTable("chat_messages") {
		utils.FileLogger.Info("chat_messages 表已存在，跳过创建")
		return
	}

	createSQL := `
	CREATE TABLE IF NOT EXISTS chat_messages (
		id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
		sender_id varchar(50) NOT NULL COMMENT '发送者用户ID',
		receiver_id varchar(50) NOT NULL COMMENT '接收者用户ID',
		content text NOT NULL COMMENT '消息内容',
		created_at datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
		PRIMARY KEY (id),
		KEY idx_chat_messages_sender_id (sender_id) COMMENT '发送者ID索引',
		KEY idx_chat_messages_receiver_id (receiver_id) COMMENT '接收者ID索引',
		KEY idx_chat_messages_created_at (created_at) COMMENT '创建时间索引',
		KEY idx_chat_messages_sender_receiver (
			sender_id,
			receiver_id,
			created_at
		) COMMENT '发送者接收者组合索引，用于查询聊天历史'
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`
	if err := config.DB.Exec(createSQL).Error; err != nil {
		utils.FileLogger.Error(fmt.Sprintf("创建 chat_messages 表失败: %v", err))
	}
	utils.FileLogger.Info("chat_messages 表不存在，已创建")
}
