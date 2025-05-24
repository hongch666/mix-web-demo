package controller

import (
	"gin_proj/service"
	"gin_proj/utils"

	"github.com/gin-gonic/gin"
)

func TestController(c *gin.Context) {
	utils.RespondSuccess(c, "Hello,I am Gin!")
}

func JavaController(c *gin.Context) {

	data, err := service.SpringService(c)
	if err != nil {
		utils.RespondError(c, 500, err.Error())
		return
	}
	utils.RespondSuccess(c, data)
}

func NestjsController(c *gin.Context) {

	data, err := service.NestjsService(c)
	if err != nil {
		utils.RespondError(c, 500, err.Error())
	}
	utils.RespondSuccess(c, data)
}
