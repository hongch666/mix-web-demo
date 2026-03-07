package main

import (
	"app/internal/boot"
)

func main() {
	// 解析命令行参数，获取配置文件路径
	configFile := boot.ParseFlags()
	// 启动 GoZero 应用服务
	boot.Run(configFile)
}
