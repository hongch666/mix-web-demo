package config

import (
	"fmt"
	"log"
	"time"

	"gin_proj/entity/po"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

func InitGorm() {
	// 数据库连接配置
	username := Config.Database.Mysql.Username
	password := Config.Database.Mysql.Password
	host := Config.Database.Mysql.Host
	port := Config.Database.Mysql.Port
	dbname := Config.Database.Mysql.Dbname
	charset := Config.Database.Mysql.Charset
	loc := Config.Database.Mysql.Loc

	// 拼接 DSN（Data Source Name）
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?charset=%s&parseTime=True&loc=%s",
		username, password, host, port, dbname, charset, loc)

	// 配置 GORM 日志模式
	newLogger := logger.New(
		log.New(log.Writer(), "\r\n", log.LstdFlags),
		logger.Config{
			SlowThreshold:             time.Second, // 慢查询阈值
			LogLevel:                  logger.Info, // 日志级别
			IgnoreRecordNotFoundError: true,        // 忽略记录未找到错误
			Colorful:                  true,        // 启用彩色打印
		},
	)

	// 连接数据库
	var err error
	DB, err = gorm.Open(mysql.Open(dsn), &gorm.Config{
		Logger: newLogger,
	})
	if err != nil {
		log.Fatalf("数据库连接失败: %v", err)
	}

	// 设置连接池
	sqlDB, err := DB.DB()
	if err != nil {
		log.Fatalf("获取数据库实例失败: %v", err)
	}
	sqlDB.SetMaxIdleConns(10)           // 设置空闲连接池中连接的最大数量
	sqlDB.SetMaxOpenConns(100)          // 设置打开数据库连接的最大数量
	sqlDB.SetConnMaxLifetime(time.Hour) // 设置连接可复用的最大时间

	log.Println("数据库连接成功")

	// 初始化表结构
	initMigrate()
}

// initMigrate 检查并按需创建表（仅在表不存在时执行 CREATE TABLE DDL）
func initMigrate() {
	if DB == nil {
		log.Println("DB 为 nil，跳过表迁移/创建")
		return
	}

	migrator := DB.Migrator()
	// 检查表是否存在
	if migrator.HasTable(&po.ChatMessage{}) || migrator.HasTable("chat_messages") {
		log.Println("chat_messages 表已存在，检查是否需要添加is_read字段")
		// 检查is_read字段是否存在，不存在则添加
		if !migrator.HasColumn(&po.ChatMessage{}, "is_read") {
			if err := migrator.AddColumn(&po.ChatMessage{}, "is_read"); err != nil {
				log.Printf("添加 is_read 字段失败: %v", err)
			} else {
				log.Println("is_read 字段已添加")
			}
		}
		return
	}

	createSQL := `
	CREATE TABLE IF NOT EXISTS chat_messages (
		id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
		sender_id varchar(50) NOT NULL COMMENT '发送者用户ID',
		receiver_id varchar(50) NOT NULL COMMENT '接收者用户ID',
		content text NOT NULL COMMENT '消息内容',
		is_read tinyint NOT NULL DEFAULT 0 COMMENT '是否已读，0为未读，1为已读',
		created_at datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
		PRIMARY KEY (id),
		KEY idx_chat_messages_sender_id (sender_id) COMMENT '发送者ID索引',
		KEY idx_chat_messages_receiver_id (receiver_id) COMMENT '接收者ID索引',
		KEY idx_chat_messages_created_at (created_at) COMMENT '创建时间索引',
		KEY idx_chat_messages_is_read (is_read) COMMENT '已读状态索引',
		KEY idx_chat_messages_sender_receiver (
			sender_id,
			receiver_id,
			created_at
		) COMMENT '发送者接收者组合索引，用于查询聊天历史'
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`
	if err := DB.Exec(createSQL).Error; err != nil {
		log.Printf("创建 chat_messages 表失败: %v", err)
	}
	log.Println("chat_messages 表不存在，已创建")
}
