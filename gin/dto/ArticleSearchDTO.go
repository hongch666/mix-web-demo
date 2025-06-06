package dto

type ArticleSearchDTO struct {
	Keyword   string  `form:"keyword"`         // 关键词，搜索title,content,tags
	UserID    *uint   `form:"userId"`          // 用户ID，可选
	StartDate *string `form:"startDate"`       // 发布时间开始时间（ISO8601字符串），可选
	EndDate   *string `form:"endDate"`         // 发布时间结束时间，可选
	Page      int     `form:"page,default=1"`  // 页码，默认1
	Size      int     `form:"size,default=10"` // 每页大小，默认10
}
