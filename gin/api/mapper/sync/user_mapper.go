package sync

import (
	"context"
	"gin_proj/common/exceptions"
	"gin_proj/common/utils"
	"gin_proj/config"
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type UserMapper struct{}

func (m *UserMapper) SearchUserByIds(userIDs []int) []po.User {
	ctx := context.Background()
	users, err := gorm.G[po.User](config.DB).Where("id IN ?", userIDs).Find(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.USER_QUERY_ERROR, err.Error()))
	}
	return users
}
