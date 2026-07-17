package types

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"app/common/constants"
	"app/common/exceptions"
)

// Validate 校验搜索文章请求参数
func (r *SearchArticlesReq) Validate() error {
	if r.UserId != nil && *r.UserId <= 0 {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.FIELD_GREATER_THAN_ZERO_ERROR, constants.USER_ID_FIELD))
	}

	if r.Page <= 0 {
		return exceptions.NewBadRequestErrorSame(constants.SEARCH_PAGE_GREATER_THAN_ZERO_ERROR)
	}

	if r.Size <= 0 {
		return exceptions.NewBadRequestErrorSame(constants.SEARCH_SIZE_GREATER_THAN_ZERO_ERROR)
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
			return exceptions.NewBadRequestErrorSame(constants.SEARCH_START_AFTER_END_ERROR)
		}
	}

	// 校验搜索模式
	if err := validateSearchMode(r.Mode); err != nil {
		return err
	}

	return nil
}

// Validate 校验搜索历史请求参数
func (r *GetSearchHistoryReq) Validate() error {
	userID := strings.TrimSpace(r.UserId)
	if userID == "" {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.FIELD_EMPTY_ERROR, constants.USER_ID_FIELD))
	}

	parsedUserID, err := strconv.ParseInt(userID, 10, 64)
	if err != nil {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.FIELD_POSITIVE_INT_ERROR, constants.USER_ID_FIELD))
	}

	if parsedUserID <= 0 {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.FIELD_GREATER_THAN_ZERO_ERROR, constants.USER_ID_FIELD))
	}

	return nil
}

func validateSearchArticlesTime(value *string, fieldName string) error {
	if value == nil {
		return nil
	}

	timeValue := strings.TrimSpace(*value)
	if timeValue == "" {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.FIELD_EMPTY_ERROR, fieldName))
	}

	if _, err := time.ParseInLocation("2006-01-02 15:04:05", timeValue, time.Local); err != nil {
		return exceptions.NewBadRequestErrorSame(fmt.Sprintf(constants.SEARCH_TIME_FORMAT_ERROR, fieldName, "2006-01-02 15:04:05"))
	}

	return nil
}

// validateSearchMode 校验搜索模式参数
func validateSearchMode(mode *string) error {
	if mode == nil || strings.TrimSpace(*mode) == "" {
		return nil
	}

	normalizedMode := strings.ToLower(strings.TrimSpace(*mode))
	switch normalizedMode {
	case "keyword", "hybrid", "graph":
		return nil
	default:
		return exceptions.NewBadRequestErrorSame(constants.SEARCH_MODE_INVALID_ERROR)
	}
}

// NormalizeSearchMode 规范化搜索模式
func NormalizeSearchMode(req *SearchArticlesReq) string {
	if req.Mode == nil || strings.TrimSpace(*req.Mode) == "" {
		return "hybrid"
	}
	return strings.ToLower(strings.TrimSpace(*req.Mode))
}

// IsVectorEnhanceEnabled 判断本次搜索是否启用向量增强
func IsVectorEnhanceEnabled(req *SearchArticlesReq, keyword string) bool {
	if NormalizeSearchMode(req) == "keyword" || strings.TrimSpace(keyword) == "" {
		return false
	}
	if req.EnableVector != nil {
		return *req.EnableVector
	}
	return true
}

// IsGraphEnhanceEnabled 判断本次搜索是否启用图谱增强
func IsGraphEnhanceEnabled(req *SearchArticlesReq) bool {
	if NormalizeSearchMode(req) == "keyword" {
		return false
	}
	if req.EnableGraph != nil {
		return *req.EnableGraph
	}
	return true
}

// IsExplainEnabled 判断是否返回搜索解释字段
func IsExplainEnabled(req *SearchArticlesReq) bool {
	if req.Explain != nil {
		return *req.Explain
	}
	return true
}
