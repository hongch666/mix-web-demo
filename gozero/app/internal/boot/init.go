package boot

import (
	"flag"

	"app/common/utils"
	"app/internal/svc"
)

const (
	// 默认配置文件路径
	DefaultConfigFile = "etc/application.yaml"
)

// ParseFlags 解析命令行标志
func ParseFlags() string {
	var configFile string
	flag.StringVar(&configFile, "f", DefaultConfigFile, utils.CONFIG_DESCRIPTION)
	flag.Parse()

	if configFile == "" {
		configFile = DefaultConfigFile
	}
	return configFile
}

// Run 启动应用服务
// 这是应用程序的主启动函数，可从 main 函数中调用
func Run(configFile string) error {
	// 加载配置
	cfg := LoadConfig(configFile)

	// 创建服务上下文
	ctx := svc.NewServiceContext(cfg)

	// 创建并初始化服务器
	server := CreateServer(cfg, ctx)
	defer server.Stop()

	// 启动服务器
	server.Start()

	return nil
}
