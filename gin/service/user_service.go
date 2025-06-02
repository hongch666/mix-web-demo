package service

import (
	"gin_proj/dto"
	"gin_proj/mapper"
	"gin_proj/po"

	"github.com/jinzhu/copier"
)

func GetUsers() ([]po.User, error) {
	users, err := mapper.GetUsers()
	if err != nil {
		return nil, err
	}
	return users, nil
}

func AddUser(userDto dto.UserCreateDTO) error {
	var user po.User
	copier.Copy(&user, &userDto)
	if err := mapper.AddUser(user); err != nil {
		return err
	}
	return nil
}

func DeleteUser(id int) error {
	return mapper.DeleteUser(id)
}

func GetUserById(id int) (po.User, error) {
	user, err := mapper.GetUserById(id)
	if err != nil {
		return po.User{}, err
	}
	return user, nil
}

func UpdateUser(userDto dto.UserUpdateDTO) error {
	var user po.User
	copier.Copy(&user, &userDto)
	if err := mapper.UpdateUser(user); err != nil {
		return err
	}
	return nil
}
