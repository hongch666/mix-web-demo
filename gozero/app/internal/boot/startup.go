package boot

import (
	"app/common/constants"
	"app/internal/config"

	"app/common/utils"

	"github.com/zeromicro/go-zero/core/logx"
)

// PrintStartupInfo 使用 ServiceContext 提供的日志实例输出服务启动信息，避免额外创建独立日志文件句柄
func PrintStartupInfo(c config.Config, logger *utils.ZeroLogger) {
	host := c.Host
	port := c.Port

	if logger == nil {
		logx.Infof(constants.SERVER_START_MESSAGE, host, port)
		logx.Infof(constants.SERVER_MODE_MESSAGE, c.Mode)
		logx.Infof(constants.SWAGGER_DOCS_MESSAGE, host, port)
		logx.Info(constants.SERVER_START_SUCCESS)
		return
	}

	logger.Infof(constants.SERVER_START_MESSAGE, host, port)
	logger.Infof(constants.SERVER_MODE_MESSAGE, c.Mode)
	logger.Infof(constants.SWAGGER_DOCS_MESSAGE, host, port)
	logger.Info(constants.SERVER_START_SUCCESS)
}
