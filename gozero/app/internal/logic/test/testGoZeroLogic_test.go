package test

import (
	"testing"

	"app/common/constants"
)

// 验证测试接口返回GoZero欢迎消息
func TestTestGoZeroReturnsWelcomeMessage(t *testing.T) {
	resp, err := (&TestGoZeroLogic{}).TestGoZero()
	if err != nil || resp.Data != constants.TEST_MESSAGE {
		t.Fatalf("测试接口响应不正确: %+v, %v", resp, err)
	}
}
