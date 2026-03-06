package articles

import (
	"context"

	"app/model"
	"gorm.io/gorm"
)

var _ ArticlesModel = (*customArticlesModel)(nil)

type (
	ArticlesModel interface {
		Insert(ctx context.Context, data *Articles) error
		FindOne(ctx context.Context, id int64) (*Articles, error)
		Update(ctx context.Context, data *Articles) error
		Delete(ctx context.Context, id int64) error
		SearchArticles(ctx context.Context) ([]Articles, error)
		GetArticleViewsByIDs(ctx context.Context, ids []int64) (map[int64]int64, error)
	}

	customArticlesModel struct {
		crud *model.GormCrud[Articles]
	}
)

// NewArticlesModel returns a model for the database table.
func NewArticlesModel(db *gorm.DB) ArticlesModel {
	return &customArticlesModel{
		crud: model.NewGormCrud[Articles](db, "articles"),
	}
}

func (m *customArticlesModel) Insert(ctx context.Context, data *Articles) error {
	return m.crud.Insert(ctx, data)
}

func (m *customArticlesModel) FindOne(ctx context.Context, id int64) (*Articles, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customArticlesModel) Update(ctx context.Context, data *Articles) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customArticlesModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customArticlesModel) SearchArticles(ctx context.Context) ([]Articles, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var articles []Articles
	err = db.Where("status = ?", 1).Find(&articles).Error
	return articles, err
}

func (m *customArticlesModel) GetArticleViewsByIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(ids) == 0 {
		return result, nil
	}

	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}

	var rows []struct {
		Id    int64 `gorm:"column:id"`
		Views int64 `gorm:"column:views"`
	}
	err = db.Select("id, views").Where("id IN ?", ids).Find(&rows).Error
	if err != nil {
		return nil, err
	}

	for _, row := range rows {
		result[row.Id] = row.Views
	}

	return result, nil
}
