package constants

import "regexp"

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

// SqlToolsMaxLimit SQL 查询最大返回行数（LIMIT 上限）
const SqlToolsMaxLimit = 100
