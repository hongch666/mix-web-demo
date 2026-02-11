package search

import (
	"net/http"
	"strconv"

	"github.com/hongch666/mix-web-demo/gin/api/service/search"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/entity/dto"

	"github.com/gin-gonic/gin"
)

type SearchController struct {
	SearchService search.SearchService
}

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
	// 绑定参数
	var searchDTO dto.ArticleSearchDTO
	if err := c.ShouldBindQuery(&searchDTO); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
	}
	ctx := c.Request.Context()
	data := con.SearchService.SearchArticles(ctx, searchDTO)
	utils.Success(c, data)
}

// @Summary 获取用户搜索历史
// @Description 获取指定用户最近10条搜索关键词列表
// @Tags 文章
// @Accept json
// @Produce json
// @Param userId path int true "用户ID"
// @Success 200 {object} map[string]interface{} "包含关键词列表的数据"
// @Failure 400 {object} map[string]interface{} "参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /search/history/{userId} [get]
func (con *SearchController) GetSearchHistoryController(c *gin.Context) {
	// 获取路径参数 userId
	userIDParam := c.Param("userId")
	userID, err := strconv.ParseInt(userIDParam, 10, 64)
	if err != nil {
		utils.Log.Error(utils.USER_ID_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.USER_ID_ERR)
		return
	}

	ctx := c.Request.Context()
	keywords, err := con.SearchService.GetSearchHistory(ctx, userID)
	if err != nil {
		utils.Log.Error(utils.SEARCH_HISTORY_FAIL + err.Error())
		utils.Error(c, http.StatusOK, utils.SEARCH_HISTORY_FAIL)
		return
	}

	utils.Success(c, map[string]any{
		"keywords": keywords,
	})
}
