package boot

import (
	"app/internal/config"

	"github.com/zeromicro/go-zero/core/logx"

	"app/common/utils"
)

// PrintStartupInfo 输出服务启动信息
func PrintStartupInfo(c config.Config) {
	logx.Infof(utils.SERVER_START_MESSAGE, c.Host, c.Port)
	logx.Infof(utils.SWAGGER_DOCS_MESSAGE, c.Host, c.Port)
	logx.Info(utils.SERVER_START_SUCCESS)
}
