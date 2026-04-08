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
		IteratePublishedArticles(ctx context.Context, batchSize int, handler func([]Articles) error) error
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
	const defaultBatchSize = 500

	articles := make([]Articles, 0, defaultBatchSize)
	err := m.IteratePublishedArticles(ctx, defaultBatchSize, func(batch []Articles) error {
		articles = append(articles, batch...)
		return nil
	})
	if err != nil {
		return nil, err
	}
	return articles, nil
}

func (m *customArticlesModel) IteratePublishedArticles(ctx context.Context, batchSize int, handler func([]Articles) error) error {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return err
	}

	if batchSize <= 0 {
		batchSize = 500
	}

	var lastID int64
	for {
		batch := make([]Articles, 0, batchSize)
		query := db.Where("status = ? AND id > ?", 1, lastID).
			Order("id ASC").
			Limit(batchSize)
		if err := query.Find(&batch).Error; err != nil {
			return err
		}
		if len(batch) == 0 {
			return nil
		}

		if err := handler(batch); err != nil {
			return err
		}

		lastID = batch[len(batch)-1].Id
	}
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
