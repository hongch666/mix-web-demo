package search

import (
	"context"
	"errors"
	"time"

	"github.com/olivere/elastic/v7"
	"go.mongodb.org/mongo-driver/mongo"
)

var (
	ErrNilESClient     = errors.New("es client is nil")
	ErrNilMongoClient  = errors.New("mongo client is nil")
	ErrEmptyMongoDB    = errors.New("mongo database is empty")
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

type SearchLog struct {
	ID        string         `bson:"_id,omitempty"`
	UserID    int64          `bson:"user_id"`
	ArticleID *int64         `bson:"article_id,omitempty"`
	Action    string         `bson:"action"`
	Content   map[string]any `bson:"content"`
	Msg       string         `bson:"msg"`
	CreatedAt time.Time      `bson:"created_at"`
	UpdatedAt time.Time      `bson:"updated_at"`
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

type ArticleViewCounter interface {
	GetArticleViewsByIDs(ctx context.Context, ids []int64) (map[int64]int64, error)
}

type LikeCounter interface {
	GetLikeCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error)
}

type CollectCounter interface {
	GetCollectCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error)
}

type FollowCounter interface {
	GetFollowCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error)
}

type SearchModelDeps struct {
	ESClient      *elastic.Client
	MongoClient   *mongo.Client
	MongoDatabase string

	ArticlesModel ArticleViewCounter
	LikesModel    LikeCounter
	CollectsModel CollectCounter
	FocusModel    FollowCounter
}

type SearchModel interface {
	SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO, esScript string, weights *SearchWeights) ([]ArticleES, int, error)
	GetSearchHistory(ctx context.Context, userID int64) ([]string, error)
}

type searchModel struct {
	esClient      *elastic.Client
	mongoClient   *mongo.Client
	mongoDatabase string

	articlesModel ArticleViewCounter
	likesModel    LikeCounter
	collectsModel CollectCounter
	focusModel    FollowCounter
}

func NewSearchModel(deps SearchModelDeps) SearchModel {
	return &searchModel{
		esClient:      deps.ESClient,
		mongoClient:   deps.MongoClient,
		mongoDatabase: deps.MongoDatabase,
		articlesModel: deps.ArticlesModel,
		likesModel:    deps.LikesModel,
		collectsModel: deps.CollectsModel,
		focusModel:    deps.FocusModel,
	}
}
