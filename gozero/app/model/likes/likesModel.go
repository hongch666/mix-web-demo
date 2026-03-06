package likes

import (
	"app/model"
	"context"

	"gorm.io/gorm"
)

var _ LikesModel = (*customLikesModel)(nil)

type (
	// LikesModel is an interface to be customized, add more methods here,
	// and implement the added methods in customLikesModel.
	LikesModel interface {
		Insert(ctx context.Context, data *Likes) error
		FindOne(ctx context.Context, id int64) (*Likes, error)
		Update(ctx context.Context, data *Likes) error
		Delete(ctx context.Context, id int64) error
		FindOneByArticleIdUserId(ctx context.Context, articleId, userId int64) (*Likes, error)
		GetLikeCountByArticleID(ctx context.Context, articleID int64) (int64, error)
		GetLikeCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error)
	}

	customLikesModel struct {
		crud *model.GormCrud[Likes]
	}
)

// NewLikesModel returns a model for the database table.
func NewLikesModel(db *gorm.DB) LikesModel {
	return &customLikesModel{
		crud: model.NewGormCrud[Likes](db, "likes"),
	}
}

func (m *customLikesModel) Insert(ctx context.Context, data *Likes) error {
	return m.crud.Insert(ctx, data)
}

func (m *customLikesModel) FindOne(ctx context.Context, id int64) (*Likes, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customLikesModel) Update(ctx context.Context, data *Likes) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customLikesModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customLikesModel) FindOneByArticleIdUserId(ctx context.Context, articleId, userId int64) (*Likes, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var item Likes
	err = db.Where("article_id = ? AND user_id = ?", articleId, userId).First(&item).Error
	if err == gorm.ErrRecordNotFound {
		return nil, model.ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (m *customLikesModel) GetLikeCountByArticleID(ctx context.Context, articleID int64) (int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}
	var count int64
	err = db.Where("article_id = ?", articleID).Count(&count).Error
	return count, err
}

func (m *customLikesModel) GetLikeCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(articleIDs) == 0 {
		return result, nil
	}
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var rows []struct {
		ArticleID int64 `gorm:"column:article_id"`
		Count     int64 `gorm:"column:count"`
	}
	err = db.Select("article_id, count(*) as count").Where("article_id IN ?", articleIDs).Group("article_id").Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID] = row.Count
	}
	return result, nil
}
