package utils

type UserAddDTO struct {
	UserName  string `json:"username" binding:"required"`
	Password   string    `json:"password" binding:"required"`
	Email string `json:"email" binding:"required"`
	Address string `json:"address" binding:"required"`
}

type UserUpdateDTO struct {
	UserId int `json:"user_id" binding:"required"`
	UserName  string `json:"username" binding:"required"`
	Password   string    `json:"password" binding:"required"`
	Email string `json:"email" binding:"required"`
	Address string `json:"address" binding:"required"`
}

type AdminDTO struct {
	UserName  string `json:"username" binding:"required"`
	Password   string    `json:"password" binding:"required"`
}