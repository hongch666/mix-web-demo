package search

import (
	"context"
	"errors"

	"github.com/olivere/elastic/v7"
)

var (
	ErrNilESClient     = errors.New("es client is nil")
	ErrSearchHitsEmpty = errors.New("es search hits is nil")
)

type ArticleSearchDTO struct {
	Keyword         string  `form:"keyword"`
	UserID          *uint64 `form:"userId"`
	Username        string  `form:"username"`
	CategoryName    string  `form:"category_name"`
	SubCategoryName string  `form:"sub_category_name"`
	StartDate       *string `form:"startDate"`
	EndDate         *string `form:"endDate"`
	Page            int     `form:"page,default=1"`
	Size            int     `form:"size,default=10"`
}

type ArticleES struct {
	ID                int64   `json:"id"`
	Title             string  `json:"title"`
	Content           string  `json:"content"`
	UserID            int64   `json:"userId"`
	Username          string  `json:"username"`
	Tags              string  `json:"tags"`
	Status            int     `json:"status"`
	Views             int     `json:"views"`
	LikeCount         int     `json:"likeCount"`
	CollectCount      int     `json:"collectCount"`
	AuthorFollowCount int     `json:"authorFollowCount"`
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

type SearchContent struct {
	Keyword         string  `json:"Keyword"`
	UserID          *int64  `json:"UserID"`
	Username        string  `json:"Username"`
	CategoryName    string  `json:"CategoryName"`
	SubCategoryName string  `json:"SubCategoryName"`
	StartDate       *string `json:"StartDate"`
	EndDate         *string `json:"EndDate"`
	Page            int     `json:"Page"`
	Size            int     `json:"Size"`
}

type SearchModelConfig struct {
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
}

type ArticleStatsProvider interface {
	GetSearchStats(ctx context.Context, articleIDs []int64) (map[int64]ArticleStats, error)
}

type SearchModelDeps struct {
	ESClient      *elastic.Client
	Config        SearchModelConfig
	StatsProvider ArticleStatsProvider
}

type SearchModel interface {
	SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO) ([]ArticleES, int, error)
}

type searchModel struct {
	esClient      *elastic.Client
	config        SearchModelConfig
	statsProvider ArticleStatsProvider
}

func NewSearchModel(deps SearchModelDeps) SearchModel {
	return &searchModel{
		esClient:      deps.ESClient,
		config:        deps.Config,
		statsProvider: deps.StatsProvider,
	}
}

type ArticleStats struct {
	Views             int
	LikeCount         int
	CollectCount      int
	AuthorFollowCount int
}
