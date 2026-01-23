package config

import (
	"log"
)

func InitMessage() {
	// 获取服务信息
	ip := Config.Server.Ip
	port := Config.Server.Port
	// 输出启动信息和Swagger地址
	log.Printf(WELCOME_MESSAGE)
	log.Printf(SERVICE_ADDRESS_MESSAGE, ip, port)
	log.Printf(SWAGGER_ADDRESS_MESSAGE, ip, port)
}
