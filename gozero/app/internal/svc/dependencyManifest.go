package svc

import (
	"fmt"
	"strings"

	"app/common/constants"

	"github.com/zeromicro/go-zero/core/logx"
)

// 依赖清单条目：required 表示缺失时是否拒绝启动
type dependencyEntry struct {
	name     string
	required bool
	missing  bool
}

// validateDependencies 在组合根装配完成后统一校验依赖清单
// 必需依赖（服务发现/聊天持久化/搜索核心）缺失时 panic 快速失败
// 可选依赖缺失时打一条聚合降级日志，服务以降级能力继续运行
func validateDependencies(ic *InfrastructureContext) {
	entries := []dependencyEntry{
		{name: "nacos", required: true, missing: ic.NamingClient == nil},
		{name: "mysql", required: true, missing: ic.MySQLConn == nil},
		{name: "elasticsearch", required: true, missing: ic.ESClient == nil},
		{name: "rabbitmq", required: false, missing: ic.RabbitMQPublisher == nil},
		{name: "redis", required: false, missing: ic.RedisClient == nil},
		{name: "mysql_raw", required: false, missing: ic.RawMySQL == nil},
	}

	missingRequired := make([]string, 0, len(entries))
	missingOptional := make([]string, 0, len(entries))
	for _, entry := range entries {
		if !entry.missing {
			continue
		}
		if entry.required {
			missingRequired = append(missingRequired, entry.name)
		} else {
			missingOptional = append(missingOptional, entry.name)
		}
	}

	if len(missingOptional) > 0 {
		logx.Errorf(constants.DEPENDENCY_MANIFEST_DEGRADED, strings.Join(missingOptional, ","))
	}
	if len(missingRequired) > 0 {
		message := fmt.Sprintf(constants.DEPENDENCY_MANIFEST_REQUIRED_MISSING, strings.Join(missingRequired, ","))
		logx.Errorf("%s", message)
		panic(message)
	}
}
