package sync

import (
	"context"

	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/config"
	"github.com/hongch666/mix-web-demo/gin/entity/po"

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
