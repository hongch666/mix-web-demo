// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package sqlTools

import (
	"context"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

// 预定义的表结构信息
var tableSchemas = map[string][]types.SqlToolsColumnInfo{
	"chat_messages": {
		{Name: "id", Type: "bigint(20) unsigned", Key: "PRI", Comment: "主键ID"},
		{Name: "sender_id", Type: "varchar(64)", Key: "MUL", Comment: "发送者ID"},
		{Name: "receiver_id", Type: "varchar(64)", Key: "MUL", Comment: "接收者ID"},
		{Name: "content", Type: "text", Key: "", Comment: "消息内容"},
		{Name: "message_type", Type: "varchar(32)", Key: "", Comment: "消息类型"},
		{Name: "is_read", Type: "tinyint(1)", Key: "", Comment: "是否已读"},
		{Name: "created_at", Type: "datetime", Key: "", Comment: "创建时间"},
		{Name: "updated_at", Type: "datetime", Key: "", Comment: "更新时间"},
	},
}

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
		columns := tableSchemas[t]
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
		return nil, exceptions.NewBadRequestErrorSame("安全限制：表 '" + tableName + "' 不在白名单内")
	}

	columns := tableSchemas[tableName]
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
