// Code scaffolded by goctl. Safe to edit.

package chat

import (
	"context"
	"fmt"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

// ChatGetAllUnreadCountsLogic 处理获取所有未读消息数接口请求的逻辑对象
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

// ChatGetAllUnreadCounts 处理获取所有未读消息数接口请求，查询用户与其他所有人的未读数并返回
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
