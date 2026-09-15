package types

import (
	"strings"
	"testing"
)

func TestChatConnectReqValidate(t *testing.T) {
	positiveUserID := int64(100)
	zeroUserID := int64(0)
	negativeUserID := int64(-5)

	cases := []struct {
		name         string
		userID       *int64
		wantErr      bool
		wantContains string
	}{
		{
			name:   "缺省允许（身份可来自请求头）",
			userID: nil,
		},
		{
			name:   "正整数通过",
			userID: &positiveUserID,
		},
		{
			name:         "零被拒绝",
			userID:       &zeroUserID,
			wantErr:      true,
			wantContains: "必须大于0",
		},
		{
			name:         "负数被拒绝",
			userID:       &negativeUserID,
			wantErr:      true,
			wantContains: "必须大于0",
		},
	}

	for _, testCase := range cases {
		t.Run("SSE/"+testCase.name, func(t *testing.T) {
			err := (&ChatSSEConnectReq{UserId: testCase.userID}).Validate()
			checkValidateResult(t, err, testCase.wantErr, testCase.wantContains)
		})

		t.Run("WebSocket/"+testCase.name, func(t *testing.T) {
			err := (&ChatWsConnectReq{UserId: testCase.userID}).Validate()
			checkValidateResult(t, err, testCase.wantErr, testCase.wantContains)
		})
	}
}

func checkValidateResult(t *testing.T, err error, wantErr bool, wantContains string) {
	t.Helper()

	if !wantErr {
		if err != nil {
			t.Fatalf("期望校验通过, 实际错误: %v", err)
		}
		return
	}

	if err == nil {
		t.Fatal("期望校验失败, 实际通过")
	}

	if !strings.Contains(err.Error(), wantContains) {
		t.Errorf("错误消息 %q 未包含期望片段 %q", err.Error(), wantContains)
	}
}
