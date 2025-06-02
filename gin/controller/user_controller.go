package controller

import (
	"gin_proj/dto"
	"gin_proj/service"
	"gin_proj/utils"
	"net/http"
	"strconv"

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

// AddUserController godoc
// @Summary 新增用户
// @Description 创建一个新用户
// @Tags 用户
// @Accept json
// @Produce json
// @Param userCreateDTO body dto.UserCreateDTO true "用户信息"
// @Success 200 {object} map[string]interface{}
// @Router /users [post]
func AddUserController(c *gin.Context) {
	var userDto dto.UserCreateDTO
	if err := c.ShouldBindJSON(&userDto); err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	err := service.AddUser(userDto)
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	utils.RespondSuccess(c, nil)
}

// DeleteUserController godoc
// @Summary 删除用户
// @Description 根据ID删除用户
// @Tags 用户
// @Accept json
// @Produce json
// @Param id path int true "用户ID"
// @Success 200 {object} map[string]interface{}
// @Router /users/{id} [delete]
func DeleteUserController(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	if err := service.DeleteUser(id); err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	utils.RespondSuccess(c, nil)
}

// GetUserByIdController godoc
// @Summary 根据ID查询用户
// @Description 根据ID查询用户
// @Tags 用户
// @Accept json
// @Produce json
// @Param id path int true "用户ID"
// @Success 200 {object} map[string]interface{}
// @Router /users/{id} [get]
func GetUserByIdController(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	user, err := service.GetUserById(id)
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	utils.RespondSuccess(c, user)
}

// UpdateUserController godoc
// @Summary 修改用户
// @Description 修改一个用户
// @Tags 用户
// @Accept json
// @Produce json
// @Param userUpdateDTO body dto.UserUpdateDTO true "用户信息"
// @Success 200 {object} map[string]interface{}
// @Router /users [put]
func UpdateUserController(c *gin.Context) {
	var userDto dto.UserUpdateDTO
	if err := c.ShouldBindJSON(&userDto); err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	err := service.UpdateUser(userDto)
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	utils.RespondSuccess(c, nil)
}
