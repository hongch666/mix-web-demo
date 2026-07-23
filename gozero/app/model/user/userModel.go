package user

import (
	"context"
	"fmt"
	"strings"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ UserModel = (*customUserModel)(nil)

type (
	UserModel interface {
		Insert(ctx context.Context, data *User) error
		FindOne(ctx context.Context, id int64) (*User, error)
		Update(ctx context.Context, data *User) error
		Delete(ctx context.Context, id int64) error
		FindOneByName(ctx context.Context, name string) (*User, error)
		FindOneByEmail(ctx context.Context, email string) (*User, error)
		SearchUserByIds(ctx context.Context, userIDs []int64) ([]User, error)
	}
	customUserModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultUserModel
	}
)

func NewUserModel(conn sqlx.SqlConn) UserModel {
	return &customUserModel{conn: conn, baseModel: newUserModel(conn)}
}
func (m *customUserModel) Insert(ctx context.Context, data *User) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customUserModel) FindOne(ctx context.Context, id int64) (*User, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customUserModel) Update(ctx context.Context, data *User) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customUserModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customUserModel) FindOneByName(ctx context.Context, name string) (*User, error) {
	return m.baseModel.FindOneByName(ctx, name)
}
func (m *customUserModel) FindOneByEmail(ctx context.Context, email string) (*User, error) {
	var item User
	query := fmt.Sprintf("select %s from %s where `email` = ? limit 1", userRows, m.baseModel.table)
	if err := m.conn.QueryRowCtx(ctx, &item, query, email); err != nil {
		return nil, err
	}
	return &item, nil
}
func (m *customUserModel) SearchUserByIds(ctx context.Context, ids []int64) ([]User, error) {
	if len(ids) == 0 {
		return []User{}, nil
	}
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	query := fmt.Sprintf("select %s from %s where `id` in (%s)", userRows, m.baseModel.table, strings.TrimRight(strings.Repeat("?,", len(ids)), ","))
	var users []User
	err := m.conn.QueryRowsCtx(ctx, &users, query, args...)
	return users, err
}
