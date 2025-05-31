package service

import (
	"gin_proj/mapper"
	"gin_proj/po"
)

func GetUsers() ([]po.User, error) {
	users, err := mapper.GetUsers()
	if err != nil {
		return nil, err
	}
	return users, nil
}
