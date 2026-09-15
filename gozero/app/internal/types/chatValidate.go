package types

import (
	"fmt"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
)

// Validate 校验发送消息请求参数
func (r *ChatSendMessageReq) Validate() error {
	if err := validatePositiveID(r.SenderId, constants.CHAT_SENDER_ID_FIELD); err != nil {
		return err
	}

	if err := validatePositiveID(r.ReceiverId, constants.CHAT_RECEIVER_ID_FIELD); err != nil {
		return err
	}

	r.Content = strings.TrimSpace(r.Content)
	if r.Content == "" {
		return exceptions.NewBadRequestErrorSame(constants.CHAT_CONTENT_EMPTY_ERROR)
	}

	return nil
}

// Validate 校验聊天历史请求参数
func (r *ChatGetHistoryReq) Validate() error {
	if err := validatePositiveID(r.UserId, constants.USER_ID_FIELD); err != nil {
		return err
	}

	if err := validatePositiveID(r.OtherId, constants.OTHER_USER_ID_FIELD); err != nil {
		return err
	}

	if r.Page <= 0 {
		return exceptions.NewBadRequestErrorSame(constants.CHAT_HISTORY_PAGE_GREATER_THAN_ZERO_ERROR)
	}

	if r.Size <= 0 {
		return exceptions.NewBadRequestErrorSame(constants.CHAT_HISTORY_SIZE_GREATER_THAN_ZERO_ERROR)
	}

	return nil
}

// Validate 校验获取未读消息数请求参数
func (r *ChatGetUnreadCountReq) Validate() error {
	if err := validatePositiveID(r.UserId, constants.USER_ID_FIELD); err != nil {
		return err
	}

	if err := validatePositiveID(r.OtherId, constants.OTHER_USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

// Validate 校验获取所有未读消息数请求参数
func (r *ChatGetAllUnreadCountsReq) Validate() error {
	if err := validatePositiveID(r.UserId, constants.USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

// Validate 校验加入队列请求参数
func (r *ChatJoinQueueReq) Validate() error {
	if err := validatePositiveID(r.UserId, constants.USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

// Validate 校验离开队列请求参数
func (r *ChatLeaveQueueReq) Validate() error {
	if err := validatePositiveID(r.UserId, constants.USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

func validatePositiveID(value int64, fieldName string) error {
	if value <= 0 {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.FIELD_GREATER_THAN_ZERO_ERROR, fieldName))
	}

	return nil
}

// Validate 校验SSE连接请求参数
// user_id 允许缺省：EventSource 无法自定义请求头，身份可能来自网关透传的请求头
// 因此这里只校验「提供了就必须是正整数」，身份来源的解析在 logic 层完成
func (r *ChatSSEConnectReq) Validate() error {
	return validateOptionalPositiveUserID(r.UserId)
}

// Validate 校验WebSocket连接请求参数
// user_id 允许缺省，原因同 SSE：WebSocket 握手同样无法自定义请求头
func (r *ChatWsConnectReq) Validate() error {
	return validateOptionalPositiveUserID(r.UserId)
}

// validateOptionalPositiveUserID 校验可选的用户ID参数
func validateOptionalPositiveUserID(userID *int64) error {
	if userID != nil && *userID <= 0 {
		return exceptions.NewBadRequestErrorSame(
			fmt.Sprintf(constants.FIELD_GREATER_THAN_ZERO_ERROR, constants.USER_ID_FIELD),
		)
	}

	return nil
}
