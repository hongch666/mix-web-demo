package logic

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"app/common/constants"
	"app/internal/svc"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

// SyncGraphFeaturesToRedis 从 Neo4j 读取活跃用户图谱特征 → Redis
func SyncGraphFeaturesToRedis(ctx context.Context, svcCtx *svc.ServiceContext) error {
	neo4jCfg := svcCtx.Config.Neo4j
	driver, err := neo4j.NewDriverWithContext(
		neo4jCfg.Uri,
		neo4j.BasicAuth(neo4jCfg.Username, neo4jCfg.Password, ""),
	)
	if err != nil {
		return fmt.Errorf(constants.TASK_GRAPH_CACHE_CONNECT_FAIL, err)
	}
	defer driver.Close(ctx)

	session := driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeRead})
	defer session.Close(ctx)

	result, err := session.Run(ctx, constants.NEO4J_ACTIVE_USERS_CYPHER, nil)
	if err != nil {
		return fmt.Errorf(constants.TASK_GRAPH_CACHE_ACTIVE_USER_FAIL, err)
	}

	var userIDs []int64
	for result.Next(ctx) {
		record := result.Record()
		if id, ok := record.Get("id"); ok {
			userIDs = append(userIDs, id.(int64))
		}
	}

	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(constants.TASK_GRAPH_CACHE_SYNC_START_LOG, len(userIDs)))
	}

	ttl := time.Duration(svcCtx.Config.Search.GraphRedisTTL) * time.Second
	if ttl <= 0 {
		ttl = 600 * time.Second
	}

	for _, userID := range userIDs {
		features := map[string]interface{}{
			"tag_list":             runStringListQuery(ctx, session, userID),
			"followed_ids":         runInt64ListQuery(ctx, session, userID),
			"preferred_subcat_ids": runSubCatListQuery(ctx, session, userID),
		}

		data, _ := json.Marshal(features)
		svcCtx.RedisClient.Set(ctx, fmt.Sprintf("%s:%d", constants.REDIS_GRAPH_CACHE_KEY_PREFIX, userID), data, ttl)
	}

	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(constants.TASK_GRAPH_CACHE_SYNC_DONE_LOG, len(userIDs)))
	}
	return nil
}

func runStringListQuery(ctx context.Context, session neo4j.SessionWithContext, uid int64) []string {
	result, err := session.Run(ctx, constants.NEO4J_USER_TAG_INTEREST_CYPHER,
		map[string]interface{}{"uid": uid})
	if err != nil {
		return []string{}
	}
	if result.Next(ctx) {
		if val, ok := result.Record().Get("tags"); ok {
			if list, ok := val.([]interface{}); ok {
				out := make([]string, 0, len(list))
				for _, v := range list {
					if s, ok := v.(string); ok {
						out = append(out, s)
					}
				}
				return out
			}
		}
	}
	return []string{}
}

func runInt64ListQuery(ctx context.Context, session neo4j.SessionWithContext, uid int64) []int64 {
	result, err := session.Run(ctx, constants.NEO4J_USER_FOLLOWED_AUTHORS_CYPHER,
		map[string]interface{}{"uid": uid})
	if err != nil {
		return []int64{}
	}
	if result.Next(ctx) {
		if val, ok := result.Record().Get("ids"); ok {
			if list, ok := val.([]interface{}); ok {
				out := make([]int64, 0, len(list))
				for _, v := range list {
					out = append(out, v.(int64))
				}
				return out
			}
		}
	}
	return []int64{}
}

func runSubCatListQuery(ctx context.Context, session neo4j.SessionWithContext, uid int64) []int64 {
	result, err := session.Run(ctx, constants.NEO4J_USER_PREFERRED_SUBCAT_CYPHER,
		map[string]interface{}{"uid": uid})
	if err != nil {
		return []int64{}
	}
	if result.Next(ctx) {
		if val, ok := result.Record().Get("ids"); ok {
			if list, ok := val.([]interface{}); ok {
				out := make([]int64, 0, len(list))
				for _, v := range list {
					out = append(out, v.(int64))
				}
				return out
			}
		}
	}
	return []int64{}
}
