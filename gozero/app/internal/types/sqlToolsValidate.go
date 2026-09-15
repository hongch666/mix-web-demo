package types

import (
	"fmt"
	"strings"
	"unicode/utf8"

	"app/common/constants"
	"app/common/exceptions"
)

// Validate 校验表结构查询请求参数
// 表名白名单等安全规则仍在 logic 层校验，此处只做请求边界检查
func (r *SqlToolsGetTablesReq) Validate() error {
	tableName := strings.TrimSpace(r.Table)
	if utf8.RuneCountInString(tableName) > constants.SqlToolsMaxTableNameLength {
		return exceptions.NewBadRequestErrorSame(
			fmt.Sprintf(constants.SQL_TOOLS_TABLE_NAME_TOO_LONG, constants.SqlToolsMaxTableNameLength),
		)
	}

	return nil
}

// Validate 校验SQL查询请求参数
// 只读语句前缀、表名白名单、强制 LIMIT 等安全规则仍在 logic 层校验，此处只做请求边界检查
func (r *SqlToolsQueryReq) Validate() error {
	query := strings.TrimSpace(r.Query)
	if query == "" {
		return exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_QUERY_EMPTY)
	}

	if utf8.RuneCountInString(query) > constants.SqlToolsMaxQueryLength {
		return exceptions.NewBadRequestErrorSame(
			fmt.Sprintf(constants.SQL_TOOLS_QUERY_TOO_LONG, constants.SqlToolsMaxQueryLength),
		)
	}

	return nil
}
