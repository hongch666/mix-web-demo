package constants

import (
	"fmt"
	"regexp"
)

// ===== SQL 工具常量 — 表名白名单、只读前缀白名单、正则、查询限制等 =====

// SqlToolsTableWhitelist SQL 工具允许查询的表名白名单
var SqlToolsTableWhitelist = map[string]bool{
	"chat_messages": true,
}

// SqlToolsAllowedPrefixes SQL 工具只读语句前缀白名单
var SqlToolsAllowedPrefixes = []string{
	"SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN",
}

// 表名匹配正则（FROM / JOIN 后跟表名）
var SqlToolsTableNameRegex = regexp.MustCompile(`(?i)\b(?:FROM|JOIN)\s+` + "`?" + `(\w+)` + "`?")

// LIMIT 匹配正则
var SqlToolsLimitRegex = regexp.MustCompile(`(?i)\bLIMIT\s+(\d+)`)

// 命名参数匹配正则
var SqlToolsNamedParamRegex = regexp.MustCompile(`:(\w+)`)

// 用于移除 SQL 字符串字面量，避免字符串内的 ; 被误判
var SqlToolsStringLiteralRegex = regexp.MustCompile(`'[^']*'|"[^"]*"`)

// 用于移除末尾分号
var SqlToolsTrailingSemicolonRegex = regexp.MustCompile(`;\s*$`)

// 空白字符标准化
var SqlToolsWhitespaceRegex = regexp.MustCompile(`\s+`)

// SqlToolsMaxLimit SQL 查询最大返回行数（LIMIT 上限）
const SqlToolsMaxLimit = 100

// SqlToolsMaxQueryLength SQL 查询语句最大字符数
const SqlToolsMaxQueryLength = 8000

// SqlToolsMaxTableNameLength 表名最大字符数
const SqlToolsMaxTableNameLength = 64

// ===== SQL 模板函数 =====

// SqlToolsCountRowsSQL 统计表行数 SQL 模板（表名来自白名单，使用反引号包裹避免保留字冲突）
func SqlToolsCountRowsSQL(tableName string) string {
	return fmt.Sprintf("SELECT COUNT(*) AS cnt FROM `%s` LIMIT 1", tableName)
}

// SqlToolsShowColumnsSQL 获取表结构 SQL 模板（表名来自白名单，使用反引号包裹避免保留字冲突）
func SqlToolsShowColumnsSQL(tableName string) string {
	return fmt.Sprintf("SHOW COLUMNS FROM `%s`", tableName)
}

// ===== 预定义表结构信息 =====

// SqlToolsColumnInfo 表列信息
type SqlToolsColumnInfo struct {
	Name    string
	Type    string
	Key     string
	Comment string
}

// SqlToolsTableSchemas 预定义的表结构信息（硬编码，避免每次查 information_schema）
//
// 唯一真相源：common/constants/scripts.go 中的 CREATE_CHAT_MESSAGES_TABLE_SQL
// （启动期由 initChatMessagesTable 执行）。此处字段必须与 DDL 严格一致，
// 任何表结构变更都要同步本 map，否则 /sql-tools/tables 会向 Agent 返回不存在的列。
var SqlToolsTableSchemas = map[string][]SqlToolsColumnInfo{
	"chat_messages": {
		{Name: "id", Type: "bigint unsigned", Key: "PRI", Comment: "消息ID，主键"},
		{Name: "sender_id", Type: "bigint", Key: "MUL", Comment: "发送者ID"},
		{Name: "receiver_id", Type: "bigint", Key: "MUL", Comment: "接收者ID"},
		{Name: "content", Type: "text", Key: "", Comment: "消息内容"},
		{Name: "is_read", Type: "tinyint", Key: "", Comment: "是否已读，0未读，1已读"},
		{Name: "created_at", Type: "datetime(3)", Key: "", Comment: "创建时间"},
	},
}
