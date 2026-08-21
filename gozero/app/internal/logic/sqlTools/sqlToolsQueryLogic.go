// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package sqlTools

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type SqlToolsQueryLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 执行只读参数化SQL查询
func NewSqlToolsQueryLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SqlToolsQueryLogic {
	return &SqlToolsQueryLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *SqlToolsQueryLogic) SqlToolsQuery(req *types.SqlToolsQueryReq) (resp *types.SqlToolsQueryResp, err error) {
	normalized, err := l.validateQuery(req.Query)
	if err != nil {
		return nil, err
	}

	// 将命名参数 :paramName 替换为 ? 占位符
	replacedQuery, args := l.replaceNamedParams(normalized, req.Params)

	// 执行查询
	var rows []map[string]interface{}
	if err := l.svcCtx.MySQLConn.QueryRowsCtx(l.ctx, &rows, replacedQuery, args...); err != nil {
		l.Error(constants.SQL_TOOLS_QUERY_FAILED + ": " + err.Error())
		return nil, exceptions.NewInternalServerError(constants.SQL_TOOLS_QUERY_FAILED, err.Error())
	}

	if len(rows) == 0 {
		return &types.SqlToolsQueryResp{
			Data: types.SqlToolsQueryResult{
				Columns:  []string{},
				Rows:     [][]string{},
				RowCount: 0,
			},
		}, nil
	}

	// 提取列名和行数据
	columns := make([]string, 0, len(rows[0]))
	for col := range rows[0] {
		columns = append(columns, col)
	}
	rowValues := make([][]string, 0, len(rows))
	for _, row := range rows {
		values := make([]string, len(columns))
		for i, col := range columns {
			values[i] = l.stringifyValue(row[col])
		}
		rowValues = append(rowValues, values)
	}

	return &types.SqlToolsQueryResp{
		Data: types.SqlToolsQueryResult{
			Columns:  columns,
			Rows:     rowValues,
			RowCount: len(rows),
		},
	}, nil
}

// stringifyValue 将查询结果值转换为字符串
func (l *SqlToolsQueryLogic) stringifyValue(v interface{}) string {
	if v == nil {
		return ""
	}
	switch val := v.(type) {
	case []byte:
		return string(val)
	case string:
		return val
	default:
		return fmt.Sprintf("%v", val)
	}
}

// validateQuery 校验SQL语句安全性
func (l *SqlToolsQueryLogic) validateQuery(query string) (string, error) {
	query = strings.TrimSpace(query)
	if query == "" {
		return "", exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_QUERY_EMPTY)
	}

	// 标准化空白字符
	query = constants.SqlToolsWhitespaceRegex.ReplaceAllString(query, " ")

	// 1. 检查多条语句（先移除字符串字面量，避免字符串内的 ; 被误判）
	withoutLiterals := constants.SqlToolsStringLiteralRegex.ReplaceAllString(query, "")
	if strings.Contains(withoutLiterals, ";") {
		withoutTrailing := constants.SqlToolsTrailingSemicolonRegex.ReplaceAllString(query, "")
		withoutTrailingLiterals := constants.SqlToolsStringLiteralRegex.ReplaceAllString(withoutTrailing, "")
		if strings.Contains(withoutTrailingLiterals, ";") {
			return "", exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_MULTIPLE_STATEMENTS)
		}
		query = withoutTrailing
	}

	upperQuery := strings.ToUpper(query)

	// 2. 检查语句类型
	allowed := false
	for _, prefix := range constants.SqlToolsAllowedPrefixes {
		if strings.HasPrefix(upperQuery, prefix) {
			allowed = true
			break
		}
	}
	if !allowed {
		return "", exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_FORBIDDEN_STATEMENT)
	}

	// 3. 检查表名白名单
	matches := constants.SqlToolsTableNameRegex.FindAllStringSubmatch(query, -1)
	for _, match := range matches {
		tableName := strings.ToLower(match[1])
		if !constants.SqlToolsTableWhitelist[tableName] {
			return "", exceptions.NewBadRequestErrorSame(
				fmt.Sprintf(constants.SQL_TOOLS_TABLE_NOT_ALLOWED, tableName),
			)
		}
	}

	// 4. 检查 LIMIT（含上限校验）
	limitMatch := constants.SqlToolsLimitRegex.FindStringSubmatch(query)
	if limitMatch == nil {
		return "", exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_LIMIT_REQUIRED)
	}
	limit, _ := strconv.Atoi(limitMatch[1])
	if limit > constants.SqlToolsMaxLimit {
		return "", exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_LIMIT_EXCEEDED)
	}

	// 5. 检查参数化占位符（使用正则匹配 :paramName 模式，避免字符串内 : 误判）
	if !constants.SqlToolsNamedParamRegex.MatchString(query) {
		return "", exceptions.NewBadRequestErrorSame(constants.SQL_TOOLS_PARAM_REQUIRED)
	}

	return query, nil
}

// replaceNamedParams 将命名参数 :paramName 替换为 ? 占位符
func (l *SqlToolsQueryLogic) replaceNamedParams(query string, params map[string]string) (string, []interface{}) {
	var args []interface{}
	replaced := constants.SqlToolsNamedParamRegex.ReplaceAllStringFunc(query, func(match string) string {
		name := match[1:] // 去掉冒号
		if val, ok := params[name]; ok {
			args = append(args, val)
		} else {
			args = append(args, nil)
		}
		return "?"
	})
	return replaced, args
}
