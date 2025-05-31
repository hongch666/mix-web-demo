package mapper

import (
	"gin_proj/config"
	"gin_proj/po"
)

func GetUsers() ([]po.User, error) {
	var users []po.User
	query := config.DB.Table("user").Model(&po.User{})
	if err := query.Find(&users).Error; err != nil {
		return nil, err
	}
	return users, nil
}
