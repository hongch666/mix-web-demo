package test

import (
	"github.com/hongch666/mix-web-demo/gin/api/service/test"
	task "github.com/hongch666/mix-web-demo/gin/common/task/logic"
	"github.com/hongch666/mix-web-demo/gin/common/utils"

	"github.com/gin-gonic/gin"
)

type TestController struct {
	TestService test.TestService
}

// @Summary Gin自己的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/gin [get]
func (con *TestController) TestController(c *gin.Context) {
	utils.RespondSuccess(c, utils.TEST_MESSAGE)
}

// @Summary 调用Spring的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/spring [get]
func (con *TestController) SpringController(c *gin.Context) {
	data := con.TestService.SpringService(c)
	utils.RespondSuccess(c, data)
}

// @Summary 调用NestJS的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/nestjs [get]
func (con *TestController) NestjsController(c *gin.Context) {
	data := con.TestService.NestjsService(c)
	utils.RespondSuccess(c, data)
}

// @Summary 调用FastAPI的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/fastapi [get]
func (con *TestController) FastapiController(c *gin.Context) {
	data := con.TestService.FastapiService(c)
	utils.RespondSuccess(c, data)
}

// @Summary 调用同步ES的测试
// @Description 查看是否同步成功
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/syncer [post]
func (con *TestController) SyncES(c *gin.Context) {
	task.SyncArticlesToES()
	utils.RespondSuccess(c, nil)
}
