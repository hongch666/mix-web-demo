package po

import "time"

type Focus struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	UserID    uint      `json:"userId"`
	FocusID   uint      `json:"focusId"`
	CreatedAt time.Time `json:"createdAt"`
}

func (Focus) TableName() string {
	return "focus"
}
