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
		log.Fatalf(DATABASE_CONNECTION_FAILURE_MESSAGE, err)
	}

	// 设置连接池
	sqlDB, err := DB.DB()
	if err != nil {
		log.Fatalf(DATABASE_GET_INSTANCE_FAILURE_MESSAGE, err)
	}
	sqlDB.SetMaxIdleConns(10)           // 设置空闲连接池中连接的最大数量
	sqlDB.SetMaxOpenConns(100)          // 设置打开数据库连接的最大数量
	sqlDB.SetConnMaxLifetime(time.Hour) // 设置连接可复用的最大时间

	log.Println(DATABASE_CONNECTION_SUCCESS_MESSAGE)

	// 初始化表结构
	initMigrate()
}

// initMigrate 检查并按需创建表（仅在表不存在时执行 CREATE TABLE DDL）
func initMigrate() {
	if DB == nil {
		log.Println(DATABASE_MIGRATE_SKIPPED_MESSAGE)
		return
	}

	migrator := DB.Migrator()
	// 检查表是否存在
	if migrator.HasTable(&po.ChatMessage{}) || migrator.HasTable("chat_messages") {
		log.Println(TABLE_ALREADY_EXISTS_MESSAGE)
		return
	}

	createSQL := CREATE_TABLE_SQL
	if err := DB.Exec(createSQL).Error; err != nil {
		log.Printf(CREATE_TABLE_FAILURE_MESSAGE, err)
	}
	log.Println(CREATE_TABLE_SUCCESS_MESSAGE)
}
