package po

type User struct {
	ID       int    `gorm:"column:id" json:"id"`
	Password string `gorm:"column:password" json:"password"`
	Name     string `gorm:"column:name" json:"name"`
	Age      int    `gorm:"column:age" json:"age"`
	Email    string `gorm:"column:email" json:"email"`
	Role     string `gorm:"column:role" json:"role"`
	Image    string `gorm:"column:image" json:"image"`
}

func (User) TableName() string {
	return "user"
}
