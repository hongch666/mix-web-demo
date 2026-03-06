package model

import (
	"context"
	"errors"

	"gorm.io/gorm"
)

var ErrNilDB = errors.New("gorm db is nil")

type GormCrud[T any] struct {
	db    *gorm.DB
	table string
}

func NewGormCrud[T any](db *gorm.DB, table string) *GormCrud[T] {
	return &GormCrud[T]{db: db, table: table}
}

func (m *GormCrud[T]) Query(ctx context.Context) (*gorm.DB, error) {
	if m.db == nil {
		return nil, ErrNilDB
	}
	return m.db.WithContext(ctx).Table(m.table), nil
}

func (m *GormCrud[T]) Insert(ctx context.Context, data *T) error {
	db, err := m.Query(ctx)
	if err != nil {
		return err
	}
	return db.Create(data).Error
}

func (m *GormCrud[T]) FindOne(ctx context.Context, id any) (*T, error) {
	db, err := m.Query(ctx)
	if err != nil {
		return nil, err
	}
	var entity T
	err = db.Where("id = ?", id).First(&entity).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &entity, nil
}

func (m *GormCrud[T]) Update(ctx context.Context, id any, data *T) error {
	db, err := m.Query(ctx)
	if err != nil {
		return err
	}
	return db.Where("id = ?", id).Select("*").Updates(data).Error
}

func (m *GormCrud[T]) Delete(ctx context.Context, id any) error {
	db, err := m.Query(ctx)
	if err != nil {
		return err
	}
	return db.Where("id = ?", id).Delete(new(T)).Error
}
