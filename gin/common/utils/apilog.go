package utils

import (
	"context"
	"fmt"
	"gin_proj/common/ctxkey"
)

// ApiLog 记录API日志
// ctx: 上下文
// method: HTTP方法（GET, POST等）
// endpoint: 请求的API路径
// msg: API日志信息
// args: 可选参数，格式为 [dataName, data] 或 [data]
func ApiLog(ctx context.Context, method string, endpoint string, msg string, args ...string) {
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)

	baseMsg := fmt.Sprintf("用户%d:%s %s %s: %s", userID, username, method, endpoint, msg)

	// 处理可选参数
	if len(args) >= 2 {
		// 传入了 dataName 和 data
		dataName, data := args[0], args[1]
		if dataName != "" && data != "" {
			baseMsg += fmt.Sprintf("\n%s: %s", dataName, data)
		}
	} else if len(args) == 1 {
		// 只传入了 data
		data := args[0]
		if data != "" {
			baseMsg += fmt.Sprintf("\ndata: %s", data)
		}
	}

	FileLogger.Info(baseMsg)
}
