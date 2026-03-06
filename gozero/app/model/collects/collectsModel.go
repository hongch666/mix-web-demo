package collects

import (
	"app/model"
	"context"

	"gorm.io/gorm"
)

var _ CollectsModel = (*customCollectsModel)(nil)

type (
	// CollectsModel is an interface to be customized, add more methods here,
	// and implement the added methods in customCollectsModel.
	CollectsModel interface {
		Insert(ctx context.Context, data *Collects) error
		FindOne(ctx context.Context, id int64) (*Collects, error)
		Update(ctx context.Context, data *Collects) error
		Delete(ctx context.Context, id int64) error
		FindOneByArticleIdUserId(ctx context.Context, articleId, userId int64) (*Collects, error)
		GetCollectCountByArticleID(ctx context.Context, articleID int64) (int64, error)
		GetCollectCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error)
	}

	customCollectsModel struct {
		crud *model.GormCrud[Collects]
	}
)

// NewCollectsModel returns a model for the database table.
func NewCollectsModel(db *gorm.DB) CollectsModel {
	return &customCollectsModel{
		crud: model.NewGormCrud[Collects](db, "collects"),
	}
}

func (m *customCollectsModel) Insert(ctx context.Context, data *Collects) error {
	return m.crud.Insert(ctx, data)
}

func (m *customCollectsModel) FindOne(ctx context.Context, id int64) (*Collects, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customCollectsModel) Update(ctx context.Context, data *Collects) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customCollectsModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customCollectsModel) FindOneByArticleIdUserId(ctx context.Context, articleId, userId int64) (*Collects, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var item Collects
	err = db.Where("article_id = ? AND user_id = ?", articleId, userId).First(&item).Error
	if err == gorm.ErrRecordNotFound {
		return nil, model.ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (m *customCollectsModel) GetCollectCountByArticleID(ctx context.Context, articleID int64) (int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}
	var count int64
	err = db.Where("article_id = ?", articleID).Count(&count).Error
	return count, err
}

func (m *customCollectsModel) GetCollectCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error) {
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
