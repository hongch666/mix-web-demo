// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"context"
	"fmt"

	"app/common/exceptions"
	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type GetSearchHistoryLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	logger *logger.ZeroLogger
}

// 获取搜索历史
func NewGetSearchHistoryLogic(ctx context.Context, svcCtx *svc.ServiceContext) *GetSearchHistoryLogic {
	return &GetSearchHistoryLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
		logger: svcCtx.Logger,
	}
}

func (l *GetSearchHistoryLogic) GetSearchHistory(req *types.GetSearchHistoryReq) (resp *types.GetSearchHistoryResp, err error) {
	// 从路径参数中解析userID
	userIDStr := req.UserId

	// 将字符串转换为int64
	userID := int64(0)
	_, err = fmt.Sscanf(userIDStr, "%d", &userID)
	if err != nil {
		l.logger.Error(fmt.Sprintf(utils.PARAM_ERR+": %v", err))
		panic(exceptions.NewBusinessError(utils.PARAM_ERR, err.Error()))
	}

	// 获取搜索历史
	keywords, err := l.svcCtx.SearchModel.GetSearchHistory(l.ctx, userID)
	if err != nil {
		l.logger.Error(fmt.Sprintf(utils.SEARCH_HISTORY_FAIL+": %v", err))
		panic(exceptions.NewBusinessError(utils.SEARCH_HISTORY_FAIL, err.Error()))
	}

	if keywords == nil {
		keywords = []string{}
	}

	resp = &types.GetSearchHistoryResp{
		Keywords: keywords,
	}

	return
}
