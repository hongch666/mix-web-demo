package aiHistory

import (
	"context"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
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
		baseModel *defaultAiHistoryModel
	}
)

func NewAiHistoryModel(conn sqlx.SqlConn) AiHistoryModel {
	return &customAiHistoryModel{baseModel: newAiHistoryModel(conn)}
}

func (m *customAiHistoryModel) Insert(ctx context.Context, data *AiHistory) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}

func (m *customAiHistoryModel) FindOne(ctx context.Context, id int64) (*AiHistory, error) {
	return m.baseModel.FindOne(ctx, id)
}

func (m *customAiHistoryModel) Update(ctx context.Context, data *AiHistory) error {
	return m.baseModel.Update(ctx, data)
}

func (m *customAiHistoryModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
