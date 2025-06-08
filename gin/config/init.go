package config

import "log"

func Init() {
	// 设置log输出格式
	log.SetFlags(0)
	log.SetPrefix("[GIN-debug] ")
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
}
