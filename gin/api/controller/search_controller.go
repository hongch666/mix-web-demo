package controller

import (
	"encoding/json"
	"fmt"
	"gin_proj/api/service"
	"gin_proj/common/ctxkey"
	"gin_proj/common/utils"
	"gin_proj/entity/dto"

	"github.com/gin-gonic/gin"
)

type SearchController struct{}

// @Summary 搜索文章
// @Description 根据关键词、用户ID、用户名、发布时间范围等条件搜索文章（支持分页）
// @Tags 文章
// @Accept json
// @Produce json
// @Param keyword query string false "搜索关键词（标题/内容/标签）"
// @Param userId query int false "用户ID"
// @Param username query string false "用户名（模糊搜索）"
// @Param startDate query string false "发布时间开始（RFC3339格式）"
// @Param endDate query string false "发布时间结束（RFC3339格式）"
// @Param page query int false "页码（默认1）"
// @Param size query int false "每页数量（默认10）"
// @Success 200 {object} map[string]interface{} "包含 total 和 list 的文章列表"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /search [get]
func (con *SearchController) SearchArticlesController(c *gin.Context) {
	// service 注入
	searchService := service.Group.SearchService
	// 绑定参数
	var searchDTO dto.ArticleSearchDTO
	if err := c.ShouldBindQuery(&searchDTO); err != nil {
		panic("参数绑定错误：" + err.Error())
	}
	dtoString, err := json.Marshal(searchDTO)
	if err != nil {
		panic("参数序列化错误：" + err.Error())
	}
	ctx := c.Request.Context()
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	username, _ := ctx.Value(ctxkey.UsernameKey).(string)
	msg := fmt.Sprintf("用户%d:%s ", userID, username)
	utils.FileLogger.Info(msg + "GET /search: " + "搜索文章\nsearchDTO: " + string(dtoString))
	data := searchService.SearchArticles(ctx, searchDTO)
	utils.RespondSuccess(c, data)
}
