package test

import (
	"fmt"
	"gin_proj/api/service"
	"gin_proj/common/ctxkey"
	"gin_proj/common/syncer"
	"gin_proj/common/utils"

	"github.com/gin-gonic/gin"
)

type TestController struct{}

// @Summary Gin自己的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/gin [get]
func (con *TestController) TestController(c *gin.Context) {
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "GET /api_gin/gin: " + "测试Gin服务")
	utils.RespondSuccess(c, "Hello,I am Gin!")
}

// @Summary 调用Spring的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/spring [get]
func (con *TestController) SpringController(c *gin.Context) {
	// service注入
	testService := service.Group.TestService
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "GET /api_gin/spring: " + "测试Spring服务")
	data := testService.SpringService(c)
	utils.RespondSuccess(c, data)
}

// @Summary 调用NestJS的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/nestjs [get]
func (con *TestController) NestjsController(c *gin.Context) {
	// service注入
	testService := service.Group.TestService
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "GET /api_gin/nestjs: " + "测试NestJS服务")
	data := testService.NestjsService(c)
	utils.RespondSuccess(c, data)
}

// @Summary 调用FastAPI的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gin/fastapi [get]
func (con *TestController) FastapiController(c *gin.Context) {
	// service注入
	testService := service.Group.TestService
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "GET /api_gin/fastapi: " + "测试FastAPI服务")
	data := testService.FastapiService(c)
	utils.RespondSuccess(c, data)
}

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
	syncer.SyncArticlesToES()
	utils.RespondSuccess(c, nil)
}
