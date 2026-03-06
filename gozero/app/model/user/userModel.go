package user

import (
	"context"

	"app/model"

	"gorm.io/gorm"
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
		crud *model.GormCrud[User]
	}
)

// NewUserModel returns a model for the database table.
func NewUserModel(db *gorm.DB) UserModel {
	return &customUserModel{
		crud: model.NewGormCrud[User](db, "user"),
	}
}

func (m *customUserModel) Insert(ctx context.Context, data *User) error {
	return m.crud.Insert(ctx, data)
}

func (m *customUserModel) FindOne(ctx context.Context, id int64) (*User, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customUserModel) Update(ctx context.Context, data *User) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customUserModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customUserModel) FindOneByName(ctx context.Context, name string) (*User, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var item User
	err = db.Where("name = ?", name).First(&item).Error
	if err == gorm.ErrRecordNotFound {
		return nil, model.ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (m *customUserModel) FindOneByEmail(ctx context.Context, email string) (*User, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var item User
	err = db.Where("email = ?", email).First(&item).Error
	if err == gorm.ErrRecordNotFound {
		return nil, model.ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (m *customUserModel) SearchUserByIds(ctx context.Context, userIDs []int64) ([]User, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var users []User
	err = db.Where("id IN ?", userIDs).Find(&users).Error
	return users, err
}
