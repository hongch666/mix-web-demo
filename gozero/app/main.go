package main

import (
	"app/internal/boot"
)

func main() {
	// 获取配置文件路径
	configFile := boot.GetConfigFilePath()
	// 启动 GoZero 应用服务
	boot.Run(configFile)
}
