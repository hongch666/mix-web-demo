// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"app/common/constants"
	"context"
	"fmt"

	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatGetAllUnreadCountsLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 获取所有未读消息数
func NewChatGetAllUnreadCountsLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetAllUnreadCountsLogic {
	return &ChatGetAllUnreadCountsLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *ChatGetAllUnreadCountsLogic) ChatGetAllUnreadCounts(req *types.ChatGetAllUnreadCountsReq) (resp *types.ChatGetAllUnreadCountsResp, err error) {
	// 获取用户与其他所有人的未读消息数
	unreadCounts, err := l.svcCtx.ChatMessagesModel.GetAllUnreadCounts(l.ctx, req.UserId)
	if err != nil {
		l.Error(fmt.Sprintf(constants.GET_ALL_UNREAD_COUNTS_ERROR+": %v", err))
		return nil, exceptions.NewInternalServerError(constants.GET_ALL_UNREAD_COUNTS_ERROR, err.Error())
	}

	l.Info(constants.GET_ALL_UNREAD_COUNTS_SUCCESS)

	resp = &types.ChatGetAllUnreadCountsResp{
		Data: unreadCounts,
	}

	return
}
