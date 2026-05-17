// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package agent

import (
	"context"

	"app/internal/svc"
	"app/internal/types"
)

type AgentTablesLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

func NewAgentTablesLogic(ctx context.Context, svcCtx *svc.ServiceContext) *AgentTablesLogic {
	return &AgentTablesLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *AgentTablesLogic) AgentTables(req *types.AgentTablesReq) (resp *types.AgentTablesResp, err error) {
	tables := []types.AgentTableItem{}
	if req.Name == "" || req.Name == "chat_messages" {
		tables = append(tables, types.AgentTableItem{
			TableName: "chat_messages",
			Columns: []types.AgentColumnItem{
				{Name: "id", Type: "BIGINT UNSIGNED", Nullable: false},
				{Name: "sender_id", Type: "VARCHAR", Nullable: false},
				{Name: "receiver_id", Type: "VARCHAR", Nullable: false},
				{Name: "content", Type: "TEXT", Nullable: false},
				{Name: "is_read", Type: "TINYINT", Nullable: false, Default: "0"},
				{Name: "created_at", Type: "DATETIME", Nullable: false, Default: "CURRENT_TIMESTAMP"},
			},
			PrimaryKey: []string{"id"},
			Indexes: []types.AgentIndexItem{
				{Name: "idx_sender_receiver", Columns: []string{"sender_id", "receiver_id"}},
				{Name: "idx_receiver_read", Columns: []string{"receiver_id", "is_read"}},
			},
		})
	}

	return &types.AgentTablesResp{Tables: tables}, nil
}
