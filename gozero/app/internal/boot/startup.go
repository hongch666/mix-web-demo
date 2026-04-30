package boot

import (
	"app/internal/config"

	"app/common/utils"

	"github.com/zeromicro/go-zero/core/logx"
)

// PrintStartupInfo 输出服务启动信息
func PrintStartupInfo(c config.Config) {
	host := utils.INIT_IP
	port := c.Port
	logger, err := utils.NewZeroLogger(c.Logs.Path)
	if err != nil {
		logx.Errorf(utils.ZERO_LOGGER_INIT_FAIL, err)
		panic(err)
	}
	logger.Infof(utils.SERVER_START_MESSAGE, host, port)
	logger.Infof(utils.SWAGGER_DOCS_MESSAGE, host, port)
	logger.Info(utils.SERVER_START_SUCCESS)
}
