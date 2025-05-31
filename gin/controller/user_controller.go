package controller

import (
	"gin_proj/service"
	"gin_proj/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

func GetUsersController(c *gin.Context) {
	users, err := service.GetUsers()
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	utils.RespondSuccess(c, users)
}
