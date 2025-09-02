package controller

import (
	"fmt"
	"gin_proj/common/ctxkey"
	"gin_proj/common/syncer"
	"gin_proj/common/utils"

	"github.com/gin-gonic/gin"
)

// @Summary 调用同步ES的测试
// @Description 查看是否同步成功
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/syncer [post]
func SyncES(c *gin.Context) {
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "POST /api_gin/syncer: " + "同步ES服务")
	syncer.SyncArticlesToES(c)
	utils.RespondSuccess(c, nil)
}
