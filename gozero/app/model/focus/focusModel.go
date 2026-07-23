package focus

import (
	"context"
	"fmt"
	"strings"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ FocusModel = (*customFocusModel)(nil)

type (
	FocusModel interface {
		Insert(context.Context, *Focus) error
		FindOne(context.Context, int64) (*Focus, error)
		Update(context.Context, *Focus) error
		Delete(context.Context, int64) error
		FindOneByUserIdFocusId(context.Context, int64, int64) (*Focus, error)
		FindOneByFocuserIdFocusedId(context.Context, int64, int64) (*Focus, error)
		GetFocusCountByUserID(context.Context, int64) (int64, error)
		GetFocusedCountByUserID(context.Context, int64) (int64, error)
		GetFocusCountsByUserIDs(context.Context, []int64) (map[int64]int64, error)
		GetFocusedCountsByUserIDs(context.Context, []int64) (map[int64]int64, error)
		GetFollowCountByUserID(context.Context, int64) (int64, error)
		GetFollowCountsByUserIDs(context.Context, []int64) (map[int64]int64, error)
	}
	customFocusModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultFocusModel
	}
)

func NewFocusModel(conn sqlx.SqlConn) FocusModel {
	return &customFocusModel{conn: conn, baseModel: newFocusModel(conn)}
}
func (m *customFocusModel) Insert(ctx context.Context, data *Focus) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customFocusModel) FindOne(ctx context.Context, id int64) (*Focus, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customFocusModel) Update(ctx context.Context, data *Focus) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customFocusModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customFocusModel) FindOneByUserIdFocusId(ctx context.Context, userID, focusID int64) (*Focus, error) {
	return m.baseModel.FindOneByUserIdFocusId(ctx, userID, focusID)
}
func (m *customFocusModel) FindOneByFocuserIdFocusedId(ctx context.Context, focuserID, focusedID int64) (*Focus, error) {
	return m.FindOneByUserIdFocusId(ctx, focuserID, focusedID)
}
func (m *customFocusModel) GetFocusCountByUserID(ctx context.Context, userID int64) (int64, error) {
	return m.getCount(ctx, "user_id", userID)
}
func (m *customFocusModel) GetFocusedCountByUserID(ctx context.Context, userID int64) (int64, error) {
	return m.getCount(ctx, "focus_id", userID)
}
func (m *customFocusModel) GetFocusCountsByUserIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	return m.getCounts(ctx, "user_id", ids)
}
func (m *customFocusModel) GetFocusedCountsByUserIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	return m.getCounts(ctx, "focus_id", ids)
}
func (m *customFocusModel) GetFollowCountByUserID(ctx context.Context, userID int64) (int64, error) {
	return m.GetFocusedCountByUserID(ctx, userID)
}
func (m *customFocusModel) GetFollowCountsByUserIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	return m.GetFocusedCountsByUserIDs(ctx, ids)
}
func (m *customFocusModel) getCount(ctx context.Context, column string, userID int64) (int64, error) {
	var count int64
	err := m.conn.QueryRowCtx(ctx, &count, fmt.Sprintf("select count(*) from %s where %s = ?", m.baseModel.table, column), userID)
	return count, err
}
func (m *customFocusModel) getCounts(ctx context.Context, column string, ids []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(ids) == 0 {
		return result, nil
	}
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	var rows []struct {
		UserID int64 `db:"user_id"`
		Count  int64 `db:"count"`
	}
	query := fmt.Sprintf("select %s as user_id, count(*) as count from %s where %s in (%s) group by %s", column, m.baseModel.table, column, strings.TrimRight(strings.Repeat("?,", len(ids)), ","), column)
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, args...); err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.UserID] = row.Count
	}
	return result, nil
}
