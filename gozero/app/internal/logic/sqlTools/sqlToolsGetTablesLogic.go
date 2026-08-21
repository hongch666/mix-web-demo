// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package sqlTools

import (
	"context"
	"fmt"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type SqlToolsGetTablesLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 获取表结构信息
func NewSqlToolsGetTablesLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SqlToolsGetTablesLogic {
	return &SqlToolsGetTablesLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *SqlToolsGetTablesLogic) SqlToolsGetTables(req *types.SqlToolsGetTablesReq) (resp *types.SqlToolsGetTablesResp, err error) {
	tableName := strings.TrimSpace(req.Table)

	if tableName != "" {
		return l.getSingleTableSchema(tableName)
	}

	// 返回所有白名单表
	tables := make([]types.SqlToolsTableInfo, 0, len(constants.SqlToolsTableWhitelist))
	for t := range constants.SqlToolsTableWhitelist {
		columns := convertColumnInfo(constants.SqlToolsTableSchemas[t])
		if columns == nil {
			columns = []types.SqlToolsColumnInfo{}
		}
		tables = append(tables, types.SqlToolsTableInfo{
			Table:   t,
			Columns: columns,
		})
	}
	return &types.SqlToolsGetTablesResp{Data: tables}, nil
}

func (l *SqlToolsGetTablesLogic) getSingleTableSchema(tableName string) (*types.SqlToolsGetTablesResp, error) {
	tableName = strings.ToLower(tableName)
	if !constants.SqlToolsTableWhitelist[tableName] {
		return nil, exceptions.NewBadRequestErrorSame(
			fmt.Sprintf(constants.SQL_TOOLS_TABLE_NOT_ALLOWED, tableName),
		)
	}

	columns := convertColumnInfo(constants.SqlToolsTableSchemas[tableName])
	if columns == nil {
		columns = []types.SqlToolsColumnInfo{}
	}
	return &types.SqlToolsGetTablesResp{
		Data: []types.SqlToolsTableInfo{
			{
				Table:   tableName,
				Columns: columns,
			},
		},
	}, nil
}

// convertColumnInfo 将 constants.SqlToolsColumnInfo 转换为 types.SqlToolsColumnInfo
func convertColumnInfo(constantsColumns []constants.SqlToolsColumnInfo) []types.SqlToolsColumnInfo {
	if constantsColumns == nil {
		return nil
	}
	result := make([]types.SqlToolsColumnInfo, len(constantsColumns))
	for i, col := range constantsColumns {
		result[i] = types.SqlToolsColumnInfo{
			Name:    col.Name,
			Type:    col.Type,
			Key:     col.Key,
			Comment: col.Comment,
		}
	}
	return result
}
