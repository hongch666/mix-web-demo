package testkit

import "testing"

// ResolveUserIDCase 身份解析共享用例，覆盖查询参数优先、请求头回退与非法输入
type ResolveUserIDCase struct {
	Name         string
	ReqUserID    *int64
	HeaderUserID string
	Want         int64
	WantErr      bool
}

// resolveUserIDTestCases SSE 与 WebSocket 共用的 ResolveUserID 用例
var resolveUserIDTestCases = []ResolveUserIDCase{
	{
		Name:         "查询参数已由中间件校验并优先使用",
		ReqUserID:    ptrInt64(100),
		HeaderUserID: "999",
		Want:         100,
	},
	{
		Name:         "查询参数缺省时回退请求头",
		HeaderUserID: "200",
		Want:         200,
	},
	{
		Name:         "请求头前后空白被裁剪",
		HeaderUserID: "  300  ",
		Want:         300,
	},
	{
		Name:    "查询参数与请求头都缺省时报错",
		WantErr: true,
	},
	{
		Name:         "请求头不是数字时报错",
		HeaderUserID: "abc",
		WantErr:      true,
	},
	{
		Name:         "请求头为零时报错",
		HeaderUserID: "0",
		WantErr:      true,
	},
	{
		Name:         "请求头为负数时报错",
		HeaderUserID: "-5",
		WantErr:      true,
	},
}

// RunResolveUserIDCases 执行共享用例，resolve 由调用方注入各自请求类型的解析入口
func RunResolveUserIDCases(t *testing.T, resolve func(reqUserID *int64, headerUserID string) (int64, error)) {
	t.Helper()
	for _, testCase := range resolveUserIDTestCases {
		t.Run(testCase.Name, func(t *testing.T) {
			got, err := resolve(testCase.ReqUserID, testCase.HeaderUserID)
			checkResolveResult(t, got, err, testCase.Want, testCase.WantErr)
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

func ptrInt64(value int64) *int64 {
	return &value
}
