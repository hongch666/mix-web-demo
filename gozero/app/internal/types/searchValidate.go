package types

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"app/common/utils"
)

// Validate 校验搜索文章请求参数
func (r *SearchArticlesReq) Validate() error {
	if r.UserId != nil && *r.UserId <= 0 {
		return errors.New(fmt.Sprintf(utils.FIELD_GREATER_THAN_ZERO_ERROR, utils.USER_ID_FIELD))
	}

	if r.Page <= 0 {
		return errors.New(utils.SEARCH_PAGE_GREATER_THAN_ZERO_ERROR)
	}

	if r.Size <= 0 {
		return errors.New(utils.SEARCH_SIZE_GREATER_THAN_ZERO_ERROR)
	}

	if err := validateSearchArticlesTime(r.StartDate, "开始时间"); err != nil {
		return err
	}

	if err := validateSearchArticlesTime(r.EndDate, "结束时间"); err != nil {
		return err
	}

	if r.StartDate != nil && r.EndDate != nil {
		startTime, _ := time.ParseInLocation("2006-01-02 15:04:05", strings.TrimSpace(*r.StartDate), time.Local)
		endTime, _ := time.ParseInLocation("2006-01-02 15:04:05", strings.TrimSpace(*r.EndDate), time.Local)
		if startTime.After(endTime) {
			return errors.New(utils.SEARCH_START_AFTER_END_ERROR)
		}
	}

	return nil
}

// Validate 校验搜索历史请求参数
func (r *GetSearchHistoryReq) Validate() error {
	userID := strings.TrimSpace(r.UserId)
	if userID == "" {
		return errors.New(fmt.Sprintf(utils.FIELD_EMPTY_ERROR, utils.USER_ID_FIELD))
	}

	parsedUserID, err := strconv.ParseInt(userID, 10, 64)
	if err != nil {
		return errors.New(fmt.Sprintf(utils.FIELD_POSITIVE_INT_ERROR, utils.USER_ID_FIELD))
	}

	if parsedUserID <= 0 {
		return errors.New(fmt.Sprintf(utils.FIELD_GREATER_THAN_ZERO_ERROR, utils.USER_ID_FIELD))
	}

	return nil
}

func validateSearchArticlesTime(value *string, fieldName string) error {
	if value == nil {
		return nil
	}

	timeValue := strings.TrimSpace(*value)
	if timeValue == "" {
		return errors.New(fmt.Sprintf(utils.FIELD_EMPTY_ERROR, fieldName))
	}

	if _, err := time.ParseInLocation("2006-01-02 15:04:05", timeValue, time.Local); err != nil {
		return errors.New(fmt.Sprintf(utils.SEARCH_TIME_FORMAT_ERROR, fieldName, "2006-01-02 15:04:05"))
	}

	return nil
}
