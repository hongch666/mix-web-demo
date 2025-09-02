package po

type Category struct {
	ID         int    `gorm:"column:id" json:"id"`
	Name       string `gorm:"column:name" json:"name"`
	CreateTime string `gorm:"column:create_time" json:"createTime"`
	UpdateTime string `gorm:"column:update_time" json:"updateTime"`
}

func (Category) TableName() string {
	return "category"
}
