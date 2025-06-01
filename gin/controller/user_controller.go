package controller

import (
	"gin_proj/service"
	"gin_proj/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

// @Summary 获取用户信息
// @Description 获取用户列表
// @Tags 用户
// @Success 200 {object} map[string]interface{}
// @Router /users [get]
func GetUsersController(c *gin.Context) {
	users, err := service.GetUsers()
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	utils.RespondSuccess(c, users)
}
