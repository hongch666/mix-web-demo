package sqlTools

import "testing"

// 验证表结构查询忽略大小写并拒绝非白名单表
func TestGetSingleTableSchemaValidatesWhitelist(t *testing.T) {
	logic := &SqlToolsGetTablesLogic{}
	if _, err := logic.getSingleTableSchema("forbidden"); err == nil {
		t.Fatal("非白名单表应被拒绝")
	}
	resp, err := logic.getSingleTableSchema("CHAT_MESSAGES")
	if err != nil || len(resp.Data) != 1 || resp.Data[0].Table != "chat_messages" {
		t.Fatalf("白名单表结构结果不正确: %+v, %v", resp, err)
	}
}
