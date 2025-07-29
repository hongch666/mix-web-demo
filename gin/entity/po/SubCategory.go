package po

type SubCategory struct {
	ID         int    `gorm:"column:id" json:"id"`
	Name       string `gorm:"column:name" json:"name"`
	CategoryID int    `gorm:"column:category_id" json:"categoryId"`
	CreateTime string `gorm:"column:create_time" json:"createTime"`
	UpdateTime string `gorm:"column:update_time" json:"updateTime"`
}

func (SubCategory) TableName() string {
	return "sub_category"
}
