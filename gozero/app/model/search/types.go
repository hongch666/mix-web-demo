package search

import (
	"context"
	"errors"

	"app/internal/client/springClient"

	"github.com/olivere/elastic/v7"
)

var (
	ErrNilESClient     = errors.New("es client is nil")
	ErrSearchHitsEmpty = errors.New("es search hits is nil")
)

type ArticleSearchDTO struct {
	Keyword         string  `form:"keyword"`
	UserID          *uint64 `form:"user_id"`
	Username        string  `form:"username"`
	CategoryName    string  `form:"category_name"`
	SubCategoryName string  `form:"sub_category_name"`
	StartDate       *string `form:"start_date"`
	EndDate         *string `form:"end_date"`
	Page            int     `form:"page,default=1"`
	Size            int     `form:"size,default=10"`
}

type ArticleES struct {
	ID                int64   `json:"id"`
	Title             string  `json:"title"`
	Content           string  `json:"content"`
	UserID            int64   `json:"user_id"`
	Username          string  `json:"username"`
	Tags              string  `json:"tags"`
	Status            int     `json:"status"`
	Views             int     `json:"views"`
	LikeCount         int     `json:"like_count"`
	CollectCount      int     `json:"collect_count"`
	AuthorFollowCount int     `json:"author_follow_count"`
	CategoryName      string  `json:"category_name"`
	SubCategoryName   string  `json:"sub_category_name"`
	CreateAt          string  `json:"create_at"`
	UpdateAt          string  `json:"update_at"`
	AIScore           float64 `json:"ai_score"`
	UserScore         float64 `json:"user_score"`
	AICommentCount    int     `json:"ai_comment_count"`
	UserCommentCount  int     `json:"user_comment_count"`
	ESScore           float64 `json:"-"` // ES 原始评分（不序列化到 JSON）
}

// SearchWeights 搜索权重（从 FastAPI 获取）
type SearchWeights struct {
	ESScoreWeight         float64
	AIRatingWeight        float64
	UserRatingWeight      float64
	ViewsWeight           float64
	LikesWeight           float64
	CollectsWeight        float64
	AuthorFollowWeight    float64
	RecencyWeight         float64
	MaxViewsNormalized    float64
	MaxLikesNormalized    float64
	MaxCollectsNormalized float64
	MaxFollowsNormalized  float64
	RecencyDecayDays      int64
	VectorScoreWeight     float64
	GraphScoreWeight      float64
	HybridMinESWeight     float64
}

// SearchScript ES 搜索脚本，包含使用 params.xxx 占位符的 Painless 脚本，由调用方传入权重参数后使用
type SearchScript struct {
	EsScript string
}

// ScriptParamMapping 脚本参数名映射: weight_key → script_param_name
type ScriptParamMapping map[string]string

// SearchModelDeps SearchModel 依赖项
type SearchModelDeps struct {
	ESClient     *elastic.Client
	SpringClient *springClient.SpringClient
}

type SearchModel interface {
	SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO, esScript string, weights *SearchWeights, paramMap ScriptParamMapping) ([]ArticleES, int, error)
}

type searchModel struct {
	esClient     *elastic.Client
	springClient *springClient.SpringClient
}

func NewSearchModel(deps SearchModelDeps) SearchModel {
	return &searchModel{
		esClient:     deps.ESClient,
		springClient: deps.SpringClient,
	}
}
