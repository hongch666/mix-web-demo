// Code scaffolded by goctl. Safe to edit.

package search

import (
	"context"
	"fmt"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/client/nestjsClient"
	"app/internal/svc"
	"app/internal/types"
)

type GetSearchHistoryLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 获取搜索历史
func NewGetSearchHistoryLogic(ctx context.Context, svcCtx *svc.ServiceContext) *GetSearchHistoryLogic {
	return &GetSearchHistoryLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *GetSearchHistoryLogic) GetSearchHistory(req *types.GetSearchHistoryReq) (resp *types.GetSearchHistoryResp, err error) {
	// 从路径参数中解析userID
	userIDStr := req.UserId

	// 将字符串转换为int64
	userID := int64(0)
	_, err = fmt.Sscanf(userIDStr, "%d", &userID)
	if err != nil {
		l.Error(fmt.Sprintf(constants.PARAM_ERR+": %v", err))
		return nil, exceptions.NewBadRequestError(constants.PARAM_ERR, err.Error())
	}

	// 通过远程调用 NestJS 内部接口获取搜索历史
	result, err := l.svcCtx.NestjsClient.GetSearchHistory(l.ctx, userID)
	if err != nil {
		l.Error(fmt.Sprintf(constants.SEARCH_HISTORY_FAIL+": %v", err))
		return nil, exceptions.NewInternalServerError(constants.SEARCH_HISTORY_FAIL, err.Error())
	}

	// 解析失败是下游契约漂移的信号，记录日志后按空历史降级，不阻断用户侧接口
	keywords, parseErr := nestjsClient.ParseSearchHistoryResult(result.Data)
	if parseErr != nil {
		l.Errorf(constants.SEARCH_HISTORY_PARSE_FAIL, parseErr)
		keywords = []string{}
	}

	resp = &types.GetSearchHistoryResp{
		Keywords: keywords,
	}

	return
}
