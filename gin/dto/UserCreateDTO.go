package dto

type UserCreateDTO struct {
	Password string `json:"password"`
	Name     string `json:"name"`
	Age      int    `json:"age"`
	Email    string `json:"email"`
}
