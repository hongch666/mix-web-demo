package types

import (
	"errors"
	"fmt"
	"strconv"
	"strings"

	"app/common/utils"
)

// Validate 校验发送消息请求参数
func (r *ChatSendMessageReq) Validate() error {
	if err := validatePositiveID(r.SenderId, utils.CHAT_SENDER_ID_FIELD); err != nil {
		return err
	}

	if err := validatePositiveID(r.ReceiverId, utils.CHAT_RECEIVER_ID_FIELD); err != nil {
		return err
	}

	r.Content = strings.TrimSpace(r.Content)
	if r.Content == "" {
		return errors.New(utils.CHAT_CONTENT_EMPTY_ERROR)
	}

	return nil
}

// Validate 校验聊天历史请求参数
func (r *ChatGetHistoryReq) Validate() error {
	if err := validatePositiveID(r.UserId, utils.USER_ID_FIELD); err != nil {
		return err
	}

	if err := validatePositiveID(r.OtherId, utils.OTHER_USER_ID_FIELD); err != nil {
		return err
	}

	if r.Page <= 0 {
		return errors.New(utils.CHAT_HISTORY_PAGE_GREATER_THAN_ZERO_ERROR)
	}

	if r.Size <= 0 {
		return errors.New(utils.CHAT_HISTORY_SIZE_GREATER_THAN_ZERO_ERROR)
	}

	return nil
}

// Validate 校验获取未读消息数请求参数
func (r *ChatGetUnreadCountReq) Validate() error {
	if err := validatePositiveID(r.UserId, utils.USER_ID_FIELD); err != nil {
		return err
	}

	if err := validatePositiveID(r.OtherId, utils.OTHER_USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

// Validate 校验获取所有未读消息数请求参数
func (r *ChatGetAllUnreadCountsReq) Validate() error {
	if err := validatePositiveID(r.UserId, utils.USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

// Validate 校验加入队列请求参数
func (r *ChatJoinQueueReq) Validate() error {
	if err := validatePositiveID(r.UserId, utils.USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

// Validate 校验离开队列请求参数
func (r *ChatLeaveQueueReq) Validate() error {
	if err := validatePositiveID(r.UserId, utils.USER_ID_FIELD); err != nil {
		return err
	}

	return nil
}

func validatePositiveID(value string, fieldName string) error {
	trimmedValue := strings.TrimSpace(value)
	if trimmedValue == "" {
		return errors.New(fmt.Sprintf(utils.FIELD_EMPTY_ERROR, fieldName))
	}

	parsedValue, err := strconv.ParseInt(trimmedValue, 10, 64)
	if err != nil {
		return errors.New(fmt.Sprintf(utils.FIELD_POSITIVE_INT_ERROR, fieldName))
	}

	if parsedValue <= 0 {
		return errors.New(fmt.Sprintf(utils.FIELD_GREATER_THAN_ZERO_ERROR, fieldName))
	}

	return nil
}
