package focus

import (
	"app/model"
	"context"

	"gorm.io/gorm"
)

var _ FocusModel = (*customFocusModel)(nil)

type (
	// FocusModel is an interface to be customized, add more methods here,
	// and implement the added methods in customFocusModel.
	FocusModel interface {
		Insert(ctx context.Context, data *Focus) error
		FindOne(ctx context.Context, id int64) (*Focus, error)
		Update(ctx context.Context, data *Focus) error
		Delete(ctx context.Context, id int64) error
		FindOneByUserIdFocusId(ctx context.Context, userId, focusId int64) (*Focus, error)
		FindOneByFocuserIdFocusedId(ctx context.Context, focuserId, focusedId int64) (*Focus, error)
		GetFocusCountByUserID(ctx context.Context, userID int64) (int64, error)
		GetFocusedCountByUserID(ctx context.Context, userID int64) (int64, error)
		GetFocusCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error)
		GetFocusedCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error)
		GetFollowCountByUserID(ctx context.Context, userID int64) (int64, error)
		GetFollowCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error)
	}

	customFocusModel struct {
		crud *model.GormCrud[Focus]
	}
)

// NewFocusModel returns a model for the database table.
func NewFocusModel(db *gorm.DB) FocusModel {
	return &customFocusModel{
		crud: model.NewGormCrud[Focus](db, "focus"),
	}
}

func (m *customFocusModel) Insert(ctx context.Context, data *Focus) error {
	return m.crud.Insert(ctx, data)
}

func (m *customFocusModel) FindOne(ctx context.Context, id int64) (*Focus, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customFocusModel) Update(ctx context.Context, data *Focus) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customFocusModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customFocusModel) FindOneByUserIdFocusId(ctx context.Context, userId, focusId int64) (*Focus, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var item Focus
	err = db.Where("user_id = ? AND focus_id = ?", userId, focusId).First(&item).Error
	if err == gorm.ErrRecordNotFound {
		return nil, model.ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (m *customFocusModel) FindOneByFocuserIdFocusedId(ctx context.Context, focuserId, focusedId int64) (*Focus, error) {
	return m.FindOneByUserIdFocusId(ctx, focuserId, focusedId)
}

func (m *customFocusModel) GetFocusCountByUserID(ctx context.Context, userID int64) (int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}
	var count int64
	err = db.Where("user_id = ?", userID).Count(&count).Error
	return count, err
}

func (m *customFocusModel) GetFocusedCountByUserID(ctx context.Context, userID int64) (int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}
	var count int64
	err = db.Where("focus_id = ?", userID).Count(&count).Error
	return count, err
}

func (m *customFocusModel) GetFocusCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(userIDs) == 0 {
		return result, nil
	}
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var rows []struct {
		UserID int64 `gorm:"column:user_id"`
		Count  int64 `gorm:"column:count"`
	}
	err = db.Select("user_id, count(*) as count").Where("user_id IN ?", userIDs).Group("user_id").Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.UserID] = row.Count
	}
	return result, nil
}

func (m *customFocusModel) GetFocusedCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(userIDs) == 0 {
		return result, nil
	}
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var rows []struct {
		UserID int64 `gorm:"column:focus_id"`
		Count  int64 `gorm:"column:count"`
	}
	err = db.Select("focus_id, count(*) as count").Where("focus_id IN ?", userIDs).Group("focus_id").Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.UserID] = row.Count
	}
	return result, nil
}

func (m *customFocusModel) GetFollowCountByUserID(ctx context.Context, userID int64) (int64, error) {
	return m.GetFocusedCountByUserID(ctx, userID)
}

func (m *customFocusModel) GetFollowCountsByUserIDs(ctx context.Context, userIDs []int64) (map[int64]int64, error) {
	return m.GetFocusedCountsByUserIDs(ctx, userIDs)
}
