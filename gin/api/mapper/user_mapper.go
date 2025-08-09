package mapper

import (
	"gin_proj/config"
	"gin_proj/entity/po"
)

func SearchUserByIds(userIDs []int) []po.User {
	var users []po.User
	if err := config.DB.Where("id IN (?)", userIDs).Find(&users).Error; err != nil {
		panic(err.Error())
	}
	return users
}
