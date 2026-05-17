// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package agent

import (
	"context"
	"database/sql"
	"fmt"
	"regexp"
	"strings"
	"time"

	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

const agentMaxRows = 500

type AgentQueryLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

func NewAgentQueryLogic(ctx context.Context, svcCtx *svc.ServiceContext) *AgentQueryLogic {
	return &AgentQueryLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *AgentQueryLogic) AgentQuery(req *types.AgentQueryReq) (resp *types.AgentQueryResp, err error) {
	query := strings.TrimSpace(req.SQL)
	if err := validateAgentSQL(query); err != nil {
		return nil, exceptions.NewBadRequestError(err.Error(), err.Error())
	}
	if l.svcCtx.DB == nil {
		return nil, exceptions.NewInternalServerError(utils.GORM_IS_NIL_MESSAGE, utils.GORM_IS_NIL_MESSAGE)
	}

	rows, err := l.svcCtx.DB.WithContext(l.ctx).Raw(appendAgentLimit(query)).Rows()
	if err != nil {
		return nil, exceptions.NewBadRequestError(err.Error(), err.Error())
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		return nil, exceptions.NewInternalServerError(err.Error(), err.Error())
	}

	resultRows, err := scanAgentRows(rows, len(columns))
	if err != nil {
		return nil, exceptions.NewInternalServerError(err.Error(), err.Error())
	}

	return &types.AgentQueryResp{
		Columns:   columns,
		Rows:      resultRows,
		TotalRows: len(resultRows),
	}, nil
}

func validateAgentSQL(query string) error {
	if query == "" {
		return fmt.Errorf(utils.AGENT_SQL_EMPTY)
	}
	normalized := strings.TrimSpace(strings.TrimRight(query, ";"))
	if strings.Contains(normalized, ";") {
		return fmt.Errorf(utils.AGENT_SQL_SINGLE_READONLY)
	}

	upper := strings.ToUpper(strings.Join(strings.Fields(normalized), " "))
	allowedPrefixes := []string{"SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"}
	allowed := false
	for _, prefix := range allowedPrefixes {
		if strings.HasPrefix(upper, prefix) {
			allowed = true
			break
		}
	}
	if !allowed {
		return fmt.Errorf(utils.AGENT_SQL_READONLY_ONLY)
	}

	tables := extractAgentTables(normalized)
	if len(tables) == 0 && !isAgentQueryWithoutTableAllowed(upper) {
		return fmt.Errorf(utils.AGENT_SQL_TABLE_SCOPE_REQUIRED)
	}
	for _, table := range tables {
		if table != "chat_messages" {
			return fmt.Errorf(utils.AGENT_SQL_TABLE_SCOPE_INVALID_PREFIX, table)
		}
	}
	return nil
}

func extractAgentTables(query string) []string {
	tablePattern := regexp.MustCompile(`(?i)\b(?:FROM|JOIN|UPDATE|INTO|TABLE|DESC|DESCRIBE)\s+` + "`?" + `([a-zA-Z_][a-zA-Z0-9_]*)` + "`?")
	matches := tablePattern.FindAllStringSubmatch(query, -1)
	tables := make([]string, 0, len(matches))
	seen := make(map[string]struct{})
	for _, match := range matches {
		if len(match) < 2 {
			continue
		}
		table := strings.ToLower(strings.Trim(match[1], "`"))
		if _, ok := seen[table]; ok {
			continue
		}
		seen[table] = struct{}{}
		tables = append(tables, table)
	}
	return tables
}

func isAgentQueryWithoutTableAllowed(upperQuery string) bool {
	return strings.HasPrefix(upperQuery, "SELECT") ||
		strings.HasPrefix(upperQuery, "WITH") ||
		strings.HasPrefix(upperQuery, "EXPLAIN SELECT") ||
		strings.HasPrefix(upperQuery, "EXPLAIN WITH")
}

func appendAgentLimit(query string) string {
	normalized := strings.TrimSpace(strings.TrimRight(query, ";"))
	upper := strings.ToUpper(normalized)
	if (strings.HasPrefix(upper, "SELECT") || strings.HasPrefix(upper, "WITH")) &&
		!regexp.MustCompile(`(?i)\bLIMIT\b`).MatchString(normalized) {
		return fmt.Sprintf("%s LIMIT %d", normalized, agentMaxRows)
	}
	return normalized
}

func scanAgentRows(rows *sql.Rows, columnCount int) ([][]string, error) {
	resultRows := make([][]string, 0)
	for rows.Next() {
		values := make([]any, columnCount)
		valuePtrs := make([]any, columnCount)
		for i := range values {
			valuePtrs[i] = &values[i]
		}
		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, err
		}
		row := make([]string, columnCount)
		for i, value := range values {
			row[i] = formatAgentValue(value)
		}
		resultRows = append(resultRows, row)
		if len(resultRows) >= agentMaxRows {
			break
		}
	}
	return resultRows, rows.Err()
}

func formatAgentValue(value any) string {
	switch v := value.(type) {
	case nil:
		return ""
	case []byte:
		return string(v)
	case time.Time:
		return v.Format("2006-01-02 15:04:05")
	default:
		return fmt.Sprint(v)
	}
}
