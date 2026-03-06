package boot

import (
	"app/internal/config"

	"github.com/joho/godotenv"
	"github.com/zeromicro/go-zero/core/conf"
)

// LoadConfig 加载配置，包括环境变量和应用配置
func LoadConfig(configFile string) config.Config {
	// 加载 .env 文件中的环境变量
	_ = godotenv.Load()

	// 读取应用配置文件
	var c config.Config
	conf.MustLoad(configFile, &c, conf.UseEnv())

	return c
}
