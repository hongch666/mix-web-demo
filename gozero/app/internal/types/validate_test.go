package types

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/validation"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// TestHttpxParseRunsTagValidation 验证 httpx.Parse 会调用注册的校验器
// 这是标签式校验生效的前提：请求类型不再实现 Validate() 后，才会走 SetValidator 分支
func TestHttpxParseRunsTagValidation(t *testing.T) {
	if err := validation.InitValidator(); err != nil {
		t.Fatalf("注册校验器失败: %v", err)
	}

	t.Run("非法参数返回业务异常", func(t *testing.T) {
		request := newJsonRequest(t, `{"sender_id":0,"receiver_id":2,"content":"你好"}`)

		var payload ChatSendMessageReq
		err := httpx.Parse(request, &payload)
		if err == nil {
			t.Fatal("期望校验失败, 实际通过")
		}

		businessErr, ok := exceptions.IsBusinessError(err)
		if !ok {
			t.Fatalf("期望业务异常, 实际类型 %T: %v", err, err)
		}
		if businessErr.BusinessCode() != constants.HttpBadRequest {
			t.Errorf("业务状态码 = %d, 期望 %d", businessErr.BusinessCode(), constants.HttpBadRequest)
		}
	})

	t.Run("合法参数通过", func(t *testing.T) {
		request := newJsonRequest(t, `{"sender_id":1,"receiver_id":2,"content":"你好"}`)

		var payload ChatSendMessageReq
		if err := httpx.Parse(request, &payload); err != nil {
			t.Fatalf("期望校验通过, 实际错误: %v", err)
		}
	})
}

// newJsonRequest 构造带 JSON 请求体的请求
func newJsonRequest(t *testing.T, body string) *http.Request {
	t.Helper()

	request := httptest.NewRequest(http.MethodPost, "/user-chat/send", strings.NewReader(body))
	request.Header.Set("Content-Type", "application/json")

	return request
}

// newTestValidator 创建生产同款校验器，用于验证 .api 中声明的校验标签真实生效
func newTestValidator(t *testing.T) *validation.RequestValidator {
	t.Helper()

	requestValidator, err := validation.NewRequestValidator()
	if err != nil {
		t.Fatalf("创建校验器失败: %v", err)
	}

	return requestValidator
}

func TestChatSendMessageReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	tests := []struct {
		name    string
		req     ChatSendMessageReq
		wantMsg string
	}{
		{name: "合法请求", req: ChatSendMessageReq{SenderId: 1, ReceiverId: 2, Content: "你好"}},
		{name: "发送者为零被拒绝", req: ChatSendMessageReq{SenderId: 0, ReceiverId: 2, Content: "你好"}, wantMsg: "必须大于"},
		{name: "接收者为零被拒绝", req: ChatSendMessageReq{SenderId: 1, ReceiverId: 0, Content: "你好"}, wantMsg: "必须大于"},
		{name: "内容为空被拒绝", req: ChatSendMessageReq{SenderId: 1, ReceiverId: 2, Content: ""}, wantMsg: "不能为空"},
		{name: "内容仅空白被拒绝", req: ChatSendMessageReq{SenderId: 1, ReceiverId: 2, Content: " \n\t "}, wantMsg: "不能为空"},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &test.req, test.wantMsg)
		})
	}
}

func TestChatGetHistoryReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	tests := []struct {
		name    string
		req     ChatGetHistoryReq
		wantMsg string
	}{
		{name: "合法请求", req: ChatGetHistoryReq{UserId: 1, OtherId: 2, Page: 1, Size: 10}},
		{name: "页码为零被拒绝", req: ChatGetHistoryReq{UserId: 1, OtherId: 2, Page: 0, Size: 10}, wantMsg: "必须大于"},
		{name: "每页数量为零被拒绝", req: ChatGetHistoryReq{UserId: 1, OtherId: 2, Page: 1, Size: 0}, wantMsg: "必须大于"},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &test.req, test.wantMsg)
		})
	}
}

func TestChatConnectReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)
	positiveUserID := int64(100)
	zeroUserID := int64(0)
	negativeUserID := int64(-5)

	tests := []struct {
		name    string
		userID  *int64
		wantMsg string
	}{
		{name: "缺省允许（身份可来自请求头）", userID: nil},
		{name: "正整数通过", userID: &positiveUserID},
		{name: "零被拒绝", userID: &zeroUserID, wantMsg: "必须大于"},
		{name: "负数被拒绝", userID: &negativeUserID, wantMsg: "必须大于"},
	}

	for _, test := range tests {
		t.Run("SSE/"+test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &ChatSSEConnectReq{UserId: test.userID}, test.wantMsg)
		})
		t.Run("WebSocket/"+test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &ChatWsConnectReq{UserId: test.userID}, test.wantMsg)
		})
	}
}

func TestSearchArticlesReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	validStart := "2026-09-01 00:00:00"
	validEnd := "2026-09-17 23:59:59"
	invalidTime := "2026/09/01"
	zeroUserID := uint64(0)
	invalidMode := "semantic"
	upperMode := " KEYWORD "

	tests := []struct {
		name    string
		req     SearchArticlesReq
		wantMsg string
	}{
		{
			name: "合法请求",
			req:  SearchArticlesReq{Page: 1, Size: 10, StartDate: &validStart, EndDate: &validEnd},
		},
		{
			name:    "用户ID必须大于零",
			req:     SearchArticlesReq{Page: 1, Size: 10, UserId: &zeroUserID},
			wantMsg: "必须大于",
		},
		{
			name:    "页码必须大于零",
			req:     SearchArticlesReq{Page: 0, Size: 10},
			wantMsg: "必须大于",
		},
		{
			name:    "每页数量必须大于零",
			req:     SearchArticlesReq{Page: 1, Size: 0},
			wantMsg: "必须大于",
		},
		{
			name:    "开始时间格式错误",
			req:     SearchArticlesReq{Page: 1, Size: 10, StartDate: &invalidTime},
			wantMsg: "格式必须为",
		},
		{
			name:    "开始时间晚于结束时间",
			req:     SearchArticlesReq{Page: 1, Size: 10, StartDate: &validEnd, EndDate: &validStart},
			wantMsg: "不能晚于",
		},
		{
			name:    "搜索模式不支持",
			req:     SearchArticlesReq{Page: 1, Size: 10, Mode: &invalidMode},
			wantMsg: "搜索模式参数无效",
		},
		{
			name: "搜索模式大小写与空白不敏感",
			req:  SearchArticlesReq{Page: 1, Size: 10, Mode: &upperMode},
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &test.req, test.wantMsg)
		})
	}
}

func TestGetSearchHistoryReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	tests := []struct {
		name    string
		userID  string
		wantMsg string
	}{
		{name: "合法用户ID", userID: "7"},
		{name: "空用户ID", userID: " ", wantMsg: "不能为空"},
		{name: "非数字用户ID", userID: "user", wantMsg: "必须是正整数"},
		{name: "零用户ID", userID: "0", wantMsg: "必须是正整数"},
		{name: "负数用户ID", userID: "-1", wantMsg: "必须是正整数"},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &GetSearchHistoryReq{UserId: test.userID}, test.wantMsg)
		})
	}
}

func TestSqlToolsQueryReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	tests := []struct {
		name    string
		query   string
		wantMsg string
	}{
		{name: "合法查询通过", query: "SELECT id FROM chat_messages LIMIT 10"},
		{name: "空查询被拒绝", query: "", wantMsg: "不能为空"},
		{name: "仅空白字符被拒绝", query: "  \n\t ", wantMsg: "不能为空"},
		{
			name:    "超长查询被拒绝",
			query:   strings.Repeat("A", 8001),
			wantMsg: "长度不能超过",
		},
		{name: "恰好达到长度上限通过", query: strings.Repeat("A", 8000)},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &SqlToolsQueryReq{Query: test.query}, test.wantMsg)
		})
	}
}

func TestSqlToolsGetTablesReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	tests := []struct {
		name    string
		table   string
		wantMsg string
	}{
		{name: "空表名合法", table: ""},
		{name: "白名单表名通过", table: "chat_messages"},
		{name: "前后空白不影响判定", table: "  chat_messages  "},
		{
			name:    "超长表名被拒绝",
			table:   strings.Repeat("t", 65),
			wantMsg: "长度不能超过",
		},
		{name: "恰好达到长度上限通过", table: strings.Repeat("t", 64)},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertRequestValid(t, requestValidator, &SqlToolsGetTablesReq{Table: test.table}, test.wantMsg)
		})
	}
}

func TestSyncESReqValidate(t *testing.T) {
	requestValidator := newTestValidator(t)

	assertRequestValid(t, requestValidator, &SyncESReq{}, "")
}

// assertRequestValid 断言请求校验结果，wantMsg 为空表示期望通过
func assertRequestValid(t *testing.T, requestValidator *validation.RequestValidator, req any, wantMsg string) {
	t.Helper()

	err := requestValidator.Validate(nil, req)
	if wantMsg == "" {
		if err != nil {
			t.Fatalf("期望校验通过, 实际错误: %v", err)
		}
		return
	}

	if err == nil {
		t.Fatal("期望校验失败, 实际通过")
	}
	if !strings.Contains(err.Error(), wantMsg) {
		t.Errorf("错误消息 %q 未包含期望片段 %q", err.Error(), wantMsg)
	}
}
