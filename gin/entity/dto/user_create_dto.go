package dto

type UserCreateDTO struct {
	Password  string `json:"password" binding:"required,min=3,max=20"`
	Name      string `json:"name" binding:"required,min=3,max=20"`
	Age       int    `json:"age" binding:"required,min=0,max=150"`
	Email     string `json:"email" binding:"required,email"`
	Img       string `json:"img" binding:"required,url"`
	Signature string `json:"signature" binding:"max=255"`
}
