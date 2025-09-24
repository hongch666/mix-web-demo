package test

import (
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
	syncer.SyncArticlesToES(c)
	utils.RespondSuccess(c, nil)
}
