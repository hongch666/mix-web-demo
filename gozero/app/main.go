package main

import (
	"os"

	"app/common/constants"
	"app/internal/boot"

	"github.com/zeromicro/go-zero/core/logx"
)

func main() {
	// 获取配置文件路径
	configFile := boot.GetConfigFilePath()
	// 启动 GoZero 应用服务，启动失败时记录日志并以非零状态码退出
	if err := boot.Run(configFile); err != nil {
		logx.Errorf(constants.SERVER_START_FAIL, err)
		os.Exit(1)
	}
}
