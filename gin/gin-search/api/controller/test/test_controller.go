package test

import (
	"fmt"
	"search/common/ctxkey"
	"search/common/syncer"
	"search/common/utils"

	"github.com/gin-gonic/gin"
)

type TestController struct{}

// @Summary 调用同步ES的测试
// @Description 查看是否同步成功
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/syncer [post]
func (con *TestController) SyncES(c *gin.Context) {
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "POST /api_gin/syncer: " + "同步ES服务")
	syncer.SyncArticlesToES(c)
	utils.RespondSuccess(c, nil)
}
