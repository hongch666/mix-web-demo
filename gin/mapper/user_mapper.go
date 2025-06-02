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

func AddUser(user po.User) error {
	return config.DB.Table("user").Create(&user).Error
}

func DeleteUser(id int) error {
	return config.DB.Table("user").Delete(&po.User{}, id).Error
}

func GetUserById(id int) (po.User, error) {
	var user po.User
	err := config.DB.Table("user").First(&user, id).Error
	if err != nil {
		return po.User{}, err
	}
	return user, nil
}

func UpdateUser(user po.User) error {
	return config.DB.Table("user").Save(&user).Error
}
