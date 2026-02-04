package config

import (
	"log"
)

func init() {
	// 设置log输出格式
	log.SetFlags(log.LstdFlags) // 建议保留时间，方便调试
	log.SetPrefix("\033[34m[GIN-debug]\033[0m ")
	// 初始化配置
	InitConfig()
	// 初始化Nacos
	InitNacos()
	// 初始化Gorm
	InitGorm()
	// 初始化ES
	InitES()
	// 初始化RabbitMQ
	InitRabbitMQ()
	// 初始化MongoDB
	InitMongoDB()
	// 初始化Goroutine监控
	InitGoroutineMonitor()
}
