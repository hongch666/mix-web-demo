package middleware

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/keys"
	"app/common/utils"

	"github.com/zeromicro/go-zero/rest/pathvar"
)

type AdminChecker interface {
	IsAdminUser(ctx context.Context, userID int64) (bool, error)
}

type AllowSelfMiddleware struct {
	adminChecker AdminChecker
	*utils.ZeroLogger
}

func NewAllowSelfMiddleware(adminChecker AdminChecker, logger *utils.ZeroLogger) *AllowSelfMiddleware {
	return &AllowSelfMiddleware{
		adminChecker: adminChecker,
		ZeroLogger:   logger,
	}
}

// Handle 允许用户访问本人数据，并允许管理员访问其他用户数据
func (m *AllowSelfMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		targetUserID, err := resolveTargetUserID(r)
		if err != nil {
			utils.HandleError(w, err)
			return
		}
		if err := requireSelfOrAdmin(r.Context(), targetUserID, m.adminChecker); err != nil {
			m.Warningf("allowSelf 权限校验失败: path=%s, targetUserId=%d, error=%v", r.URL.Path, targetUserID, err)
			utils.HandleError(w, err)
			return
		}
		next(w, r)
	}
}

func requireSelfOrAdmin(ctx context.Context, targetUserID int64, checker AdminChecker) error {
	currentUserID, _ := ctx.Value(keys.UserIDKey).(int64)
	if currentUserID <= 0 {
		return exceptions.NewUnauthorizedErrorSame(constants.USER_IDENTITY_MISSING)
	}
	if currentUserID == targetUserID {
		return nil
	}
	if checker == nil {
		return exceptions.NewForbiddenErrorSame(constants.SELF_OR_ADMIN_REQUIRED)
	}

	isAdmin, err := checker.IsAdminUser(ctx, currentUserID)
	if err != nil {
		return exceptions.NewInternalServerError(
			constants.ADMIN_PERMISSION_CHECK_FAILED,
			fmt.Sprintf("%v", err),
		)
	}
	if !isAdmin {
		return exceptions.NewForbiddenErrorSame(constants.SELF_OR_ADMIN_REQUIRED)
	}
	return nil
}

func resolveTargetUserID(r *http.Request) (int64, error) {
	targetUserID, found, err := targetUserIDFromBody(r)
	if err != nil {
		return 0, err
	}
	if found {
		return targetUserID, nil
	}
	if value := strings.TrimSpace(pathvar.Vars(r)["user_id"]); value != "" {
		return parseTargetUserID(value)
	}
	if value := strings.TrimSpace(r.URL.Query().Get("user_id")); value != "" {
		return parseTargetUserID(value)
	}

	currentUserID, _ := r.Context().Value(keys.UserIDKey).(int64)
	return currentUserID, nil
}

func targetUserIDFromBody(r *http.Request) (int64, bool, error) {
	if r.Body == nil {
		return 0, false, nil
	}
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return 0, false, exceptions.NewBadRequestError(constants.PARAM_ERR, err.Error())
	}
	r.Body = io.NopCloser(bytes.NewReader(body))
	if len(bytes.TrimSpace(body)) == 0 {
		return 0, false, nil
	}

	var fields map[string]json.RawMessage
	if err := json.Unmarshal(body, &fields); err != nil {
		return 0, false, exceptions.NewBadRequestError(constants.PARAM_ERR, err.Error())
	}
	for _, field := range []string{"user_id", "sender_id"} {
		raw, ok := fields[field]
		if !ok {
			continue
		}
		var targetUserID int64
		if err := json.Unmarshal(raw, &targetUserID); err != nil {
			return 0, false, exceptions.NewBadRequestError(constants.PARAM_ERR, err.Error())
		}
		if targetUserID <= 0 {
			return 0, false, exceptions.NewBadRequestErrorSame(constants.USER_ID_LESS)
		}
		return targetUserID, true, nil
	}
	return 0, false, nil
}

func parseTargetUserID(value string) (int64, error) {
	targetUserID, err := strconv.ParseInt(value, 10, 64)
	if err != nil || targetUserID <= 0 {
		return 0, exceptions.NewBadRequestError(
			constants.USER_ID_LESS,
			fmt.Sprintf("user_id=%q", value),
		)
	}
	return targetUserID, nil
}
