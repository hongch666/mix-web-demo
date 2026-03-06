// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"
	"fmt"

	"app/common/exceptions"
	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatGetAllUnreadCountsLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// 获取所有未读消息数
func NewChatGetAllUnreadCountsLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetAllUnreadCountsLogic {
	return &ChatGetAllUnreadCountsLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *ChatGetAllUnreadCountsLogic) ChatGetAllUnreadCounts(req *types.ChatGetAllUnreadCountsReq) (resp *types.ChatGetAllUnreadCountsResp, err error) {
	// 获取用户与其他所有人的未读消息数
	unreadCounts, err := l.svcCtx.ChatMessagesModel.GetAllUnreadCounts(l.ctx, req.UserId)
	if err != nil {
		l.Error(fmt.Sprintf(utils.GET_ALL_UNREAD_COUNTS_ERROR+": %v", err))
		panic(exceptions.NewBusinessError(utils.GET_ALL_UNREAD_COUNTS_ERROR, err.Error()))
	}

	l.Info(utils.GET_ALL_UNREAD_COUNTS_SUCCESS)

	resp = &types.ChatGetAllUnreadCountsResp{
		Data: unreadCounts,
	}

	return
}
