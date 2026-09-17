package chat

import (
	"testing"

	"app/common/utils"
	"app/internal/types"
)

func TestResolveUserID(t *testing.T) {
	logPath := t.TempDir()
	logger, err := utils.NewZeroLogger(logPath)
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	// t.Cleanup 按后进先出执行：这里注册的关闭动作会先于 t.TempDir 的目录清理，
	// 否则 Windows 下日志文件句柄未释放会导致清理失败
	t.Cleanup(func() {
		_ = logger.Close()
	})

	queryUserID := int64(100)

	cases := []struct {
		name         string
		reqUserID    *int64
		headerUserID string
		want         int64
		wantErr      bool
	}{
		{
			name:         "查询参数已由中间件校验并优先使用",
			reqUserID:    &queryUserID,
			headerUserID: "999",
			want:         100,
		},
		{
			name:         "查询参数缺省时回退请求头",
			headerUserID: "200",
			want:         200,
		},
		{
			name:         "请求头前后空白被裁剪",
			headerUserID: "  300  ",
			want:         300,
		},
		{
			name:    "查询参数与请求头都缺省时报错",
			wantErr: true,
		},
		{
			name:         "请求头不是数字时报错",
			headerUserID: "abc",
			wantErr:      true,
		},
		{
			name:         "请求头为零时报错",
			headerUserID: "0",
			wantErr:      true,
		},
		{
			name:         "请求头为负数时报错",
			headerUserID: "-5",
			wantErr:      true,
		},
	}

	sseLogic := &ChatSSELogic{ZeroLogger: logger}
	websocketLogic := &ChatWebsocketLogic{ZeroLogger: logger}

	for _, testCase := range cases {
		t.Run("SSE/"+testCase.name, func(t *testing.T) {
			req := &types.ChatSSEConnectReq{UserId: testCase.reqUserID}
			got, err := sseLogic.ResolveUserID(req, testCase.headerUserID)
			checkResolveResult(t, got, err, testCase.want, testCase.wantErr)
		})

		t.Run("WebSocket/"+testCase.name, func(t *testing.T) {
			req := &types.ChatWsConnectReq{UserId: testCase.reqUserID}
			got, err := websocketLogic.ResolveUserID(req, testCase.headerUserID)
			checkResolveResult(t, got, err, testCase.want, testCase.wantErr)
		})
	}
}

func checkResolveResult(t *testing.T, got int64, err error, want int64, wantErr bool) {
	t.Helper()

	if wantErr {
		if err == nil {
			t.Fatalf("期望解析失败, 实际得到 userID=%d", got)
		}
		return
	}

	if err != nil {
		t.Fatalf("期望解析成功, 实际错误: %v", err)
	}

	if got != want {
		t.Errorf("userID = %d, 期望 %d", got, want)
	}
}
