package cache

import (
	"context"
	"encoding/json"
	"fmt"

	"app/common/constants"

	"github.com/redis/go-redis/v9"
)

// UserGraphFeatures 用户图谱特征
type UserGraphFeatures struct {
	TagList            []string `json:"tag_list"`
	FollowedAuthorIds  []int64  `json:"followed_ids"`
	PreferredSubCatIds []int64  `json:"preferred_subcat_ids"`
}

// IsEmpty 判断图谱特征是否为空
func (f *UserGraphFeatures) IsEmpty() bool {
	return len(f.TagList) == 0 && len(f.FollowedAuthorIds) == 0 && len(f.PreferredSubCatIds) == 0
}

// GetUserGraphFeatures 从 Redis 读取用户图谱特征
func GetUserGraphFeatures(ctx context.Context, rdb *redis.Client, userID int64) (*UserGraphFeatures, error) {
	key := fmt.Sprintf("%s:%d", constants.REDIS_GRAPH_CACHE_KEY_PREFIX, userID)
	data, err := rdb.Get(ctx, key).Result()
	if err != nil {
		return &UserGraphFeatures{}, nil
	}

	var f UserGraphFeatures
	if err := json.Unmarshal([]byte(data), &f); err != nil {
		return &UserGraphFeatures{}, nil
	}
	return &f, nil
}
