package controller

import (
	"encoding/json"
	"gin_proj/dto"
	"gin_proj/service"
	"gin_proj/utils"
	"log"

	"github.com/gin-gonic/gin"
)

// @Summary 搜索文章
// @Description 根据关键词、用户ID、发布时间范围等条件搜索文章（支持分页）
// @Tags 文章
// @Accept json
// @Produce json
// @Param keyword query string false "搜索关键词（标题/内容/标签）"
// @Param userId query int false "用户ID"
// @Param startDate query string false "发布时间开始（RFC3339格式）"
// @Param endDate query string false "发布时间结束（RFC3339格式）"
// @Param page query int false "页码（默认1）"
// @Param size query int false "每页数量（默认10）"
// @Success 200 {object} map[string]interface{} "包含 total 和 list 的文章列表"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /search [get]
func SearchArticlesController(c *gin.Context) {
	var searchDTO dto.ArticleSearchDTO
	if err := c.ShouldBindQuery(&searchDTO); err != nil {
		panic("参数绑定错误：" + err.Error())
	}
	dtoString, err := json.Marshal(searchDTO)
	if err != nil {
		panic("参数序列化错误：" + err.Error())
	}
	log.Println("/search: " + "搜索文章\nsearchDTO: " + string(dtoString))
	ctx := c.Request.Context() // 获取 gin 的上下文，它带着中间件注入的值
	data := service.SearchArticles(ctx, searchDTO)
	utils.RespondSuccess(c, data)
}
