package dto

type UserUpdateDTO struct {
	ID int `json:"id" binding:"required,min=0"`
	UserCreateDTO
}
