package controller

import (
	"gin_proj/service"
	"gin_proj/syncer"
	"gin_proj/utils"

	"github.com/gin-gonic/gin"
)

// @Summary Gin自己的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/gin [get]
func TestController(c *gin.Context) {
	utils.RespondSuccess(c, "Hello,I am Gin!")
}

// @Summary 调用Spring的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/spring [get]
func JavaController(c *gin.Context) {

	data, err := service.SpringService(c)
	if err != nil {
		utils.RespondError(c, 500, err.Error())
		return
	}
	utils.RespondSuccess(c, data)
}

// @Summary 调用NestJS的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/nestjs [get]
func NestjsController(c *gin.Context) {

	data, err := service.NestjsService(c)
	if err != nil {
		utils.RespondError(c, 500, err.Error())
	}
	utils.RespondSuccess(c, data)
}

// @Summary 调用FastAPI的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/fastapi [get]
func FastapiController(c *gin.Context) {
	data, err := service.FastapiService(c)
	if err != nil {
		utils.RespondError(c, 500, err.Error())
	}
	utils.RespondSuccess(c, data)
}

// @Summary 调用同步ES的测试
// @Description 查看是否同步成功
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/syncer [post]
func SyncES(c *gin.Context) {

	err := syncer.SyncArticlesToES()
	if err != nil {
		utils.RespondError(c, 500, err.Error())
	}
	utils.RespondSuccess(c, nil)
}
