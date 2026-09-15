// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatSSELogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// SSE连接
func NewChatSSELogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatSSELogic {
	return &ChatSSELogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

// ResolveUserID 解析SSE连接的发起用户
// EventSource 无法自定义请求头，因此 user_id 优先取查询参数，缺省时回退网关注入的请求头
func (l *ChatSSELogic) ResolveUserID(req *types.ChatSSEConnectReq, headerUserID string) (int64, error) {
	if req.UserId != nil {
		return *req.UserId, nil
	}

	trimmedUserID := strings.TrimSpace(headerUserID)
	if trimmedUserID == "" {
		l.Error(constants.USER_ID_LESS)
		return 0, exceptions.NewBadRequestErrorSame(constants.USER_ID_LESS)
	}

	userID, err := strconv.ParseInt(trimmedUserID, 10, 64)
	if err != nil || userID <= 0 {
		l.Error(fmt.Sprintf(constants.USER_ID_LESS+": %v", trimmedUserID))
		return 0, exceptions.NewBadRequestErrorSame(constants.USER_ID_LESS)
	}

	return userID, nil
}
