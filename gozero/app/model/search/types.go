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
}

type SearchLog struct {
	ID        string         `bson:"_id,omitempty"`
	UserID    int64          `bson:"userId"`
	ArticleID *int64         `bson:"articleId,omitempty"`
	Action    string         `bson:"action"`
	Content   map[string]any `bson:"content"`
	Msg       string         `bson:"msg"`
	CreatedAt time.Time      `bson:"createdAt"`
	UpdatedAt time.Time      `bson:"updatedAt"`
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
	Config        SearchModelConfig

	ArticlesModel ArticleViewCounter
	LikesModel    LikeCounter
	CollectsModel CollectCounter
	FocusModel    FollowCounter
}

type SearchModel interface {
	SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO) ([]ArticleES, int, error)
	GetSearchHistory(ctx context.Context, userID int64) ([]string, error)
}

type searchModel struct {
	esClient      *elastic.Client
	mongoClient   *mongo.Client
	mongoDatabase string
	config        SearchModelConfig

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
		config:        deps.Config,
		articlesModel: deps.ArticlesModel,
		likesModel:    deps.LikesModel,
		collectsModel: deps.CollectsModel,
		focusModel:    deps.FocusModel,
	}
}
