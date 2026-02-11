package sync

import (
	"context"

	"github.com/hongch666/mix-web-demo/gin/common/config"
	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/entity/po"

	"gorm.io/gorm"
)

type FocusMapper struct{}

// GetFollowCountByUserID 根据用户ID获取该用户的关注数（粉丝数）
func (m *FocusMapper) GetFollowCountByUserID(ctx context.Context, userID int) int {
	count, err := gorm.G[po.Focus](config.DB).Where("focus_id = ?", userID).Count(ctx, "*")
	if err != nil {
		panic(exceptions.NewBusinessError(utils.FOCUS_QUERY_ERROR, err.Error()))
	}
	return int(count)
}

// GetFollowCountsByUserIDs 根据用户ID数组批量获取关注数（粉丝数）
func (m *FocusMapper) GetFollowCountsByUserIDs(ctx context.Context, userIDs []int) map[int]int {
	result := make(map[int]int)
	type CountResult struct {
		FocusID int `gorm:"column:focus_id"`
		Count   int `gorm:"column:count"`
	}
	var counts []CountResult
	err := config.DB.Model(&po.Focus{}).
		Where("focus_id IN ?", userIDs).
		Select("focus_id, count(*) as count").
		Group("focus_id").
		Scan(&counts).Error
	if err != nil {
		panic(exceptions.NewBusinessError(utils.FOCUS_QUERY_ERROR, err.Error()))
	}

	for _, item := range counts {
		result[item.FocusID] = item.Count
	}

	return result
}
