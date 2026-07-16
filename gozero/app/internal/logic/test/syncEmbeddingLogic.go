package test

import (
	"context"
	"fmt"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"
	"app/internal/types"
)

type SyncEmbeddingLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

func NewSyncEmbeddingLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SyncEmbeddingLogic {
	return &SyncEmbeddingLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *SyncEmbeddingLogic) SyncEmbedding(req *types.SyncEmbeddingReq) (resp *types.SyncEmbeddingResp, err error) {
	l.Info(constants.TASK_EMBEDDING_SYNC_MANUAL_START)

	if err = logic.SyncEmbeddingToES(l.ctx, l.svcCtx); err != nil {
		l.Error(fmt.Sprintf("%s: %v", constants.TASK_EMBEDDING_SYNC_MANUAL_FAIL, err))
		return nil, exceptions.NewInternalServerError(constants.TASK_EMBEDDING_SYNC_MANUAL_FAIL, err.Error())
	}

	l.Info(constants.TASK_EMBEDDING_SYNC_MANUAL_DONE)
	return &types.SyncEmbeddingResp{}, nil
}
