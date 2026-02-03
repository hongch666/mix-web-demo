package po

import "time"

type Focus struct {
	ID        uint      `gorm:"column:id" json:"id"`
	UserID    uint      `gorm:"column:user_id" json:"userId"`
	FocusID   uint      `gorm:"column:focus_id" json:"focusId"`
	CreatedAt time.Time `gorm:"column:created_time" json:"createdAt"`
}

func (Focus) TableName() string {
	return "focus"
}
