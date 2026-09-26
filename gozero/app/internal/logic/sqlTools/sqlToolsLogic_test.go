package sqlTools

import "testing"

// 验证SQL校验拒绝空语句、写操作和非白名单表
func TestSqlToolsQueryValidationRejectsUnsafeSQL(t *testing.T) {
	logic := &SqlToolsQueryLogic{}
	for _, query := range []string{"", "DELETE FROM articles LIMIT 1", "SELECT * FROM forbidden_table LIMIT 1"} {
		if _, err := logic.validateQuery(query); err == nil {
			t.Fatalf("SQL %q 应被拒绝", query)
		}
	}
}

// 验证命名参数按出现顺序替换为占位符
func TestReplaceNamedParamsKeepsArgumentOrder(t *testing.T) {
	logic := &SqlToolsQueryLogic{}
	query, args := logic.replaceNamedParams("SELECT * FROM articles WHERE id=:id AND title=:title LIMIT 10", map[string]string{"id": "1", "title": "Go"})
	if query != "SELECT * FROM articles WHERE id=? AND title=? LIMIT 10" || len(args) != 2 || args[0] != "1" || args[1] != "Go" {
		t.Fatalf("参数替换结果不正确: %q %#v", query, args)
	}
}

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
