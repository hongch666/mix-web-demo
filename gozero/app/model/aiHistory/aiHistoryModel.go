package aiHistory

import (
	"context"

	"app/model"
	"gorm.io/gorm"
)

var _ AiHistoryModel = (*customAiHistoryModel)(nil)

type (
	AiHistoryModel interface {
		Insert(ctx context.Context, data *AiHistory) error
		FindOne(ctx context.Context, id int64) (*AiHistory, error)
		Update(ctx context.Context, data *AiHistory) error
		Delete(ctx context.Context, id int64) error
	}

	customAiHistoryModel struct {
		crud *model.GormCrud[AiHistory]
	}
)

// NewAiHistoryModel returns a model for the database table.
func NewAiHistoryModel(db *gorm.DB) AiHistoryModel {
	return &customAiHistoryModel{
		crud: model.NewGormCrud[AiHistory](db, "ai_history"),
	}
}

func (m *customAiHistoryModel) Insert(ctx context.Context, data *AiHistory) error {
	return m.crud.Insert(ctx, data)
}

func (m *customAiHistoryModel) FindOne(ctx context.Context, id int64) (*AiHistory, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customAiHistoryModel) Update(ctx context.Context, data *AiHistory) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customAiHistoryModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}
