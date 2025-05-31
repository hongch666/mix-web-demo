package po

type User struct {
	ID       int    `gorm:"column:id"`
	Password string `gorm:"column:password"`
	Name     string `gorm:"column:name"`
	Age      int    `gorm:"column:age"`
	Email    string `gorm:"column:email"`
}
