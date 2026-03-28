package boot

import (
	"app/internal/config"

	"github.com/zeromicro/go-zero/core/logx"

	"app/common/utils"
)

// PrintStartupInfo 输出服务启动信息
func PrintStartupInfo(c config.Config) {
	host := utils.INIT_IP
	port := c.Port
	logx.Infof(utils.SERVER_START_MESSAGE, host, port)
	logx.Infof(utils.SWAGGER_DOCS_MESSAGE, host, port)
	logx.Info(utils.SERVER_START_SUCCESS)
}
