package graphreason

import (
	"fmt"
	"strings"

	"app/common/constants"
	"app/internal/cache"
	"app/internal/types"
)

// Generate 生成图谱推荐原因（按优先级取最高）
func Generate(articleID, userID int64, username, tags, subCategoryName string, uf *cache.UserGraphFeatures) string {
	if uf == nil || uf.IsEmpty() {
		return ""
	}

	if containsInt64(uf.FollowedAuthorIds, userID) {
		return fmt.Sprintf(constants.GRAPH_REASON_FOLLOWED_AUTHOR, username)
	}

	matchedTags := intersectTags(tags, uf.TagList)
	if len(matchedTags) > 0 {
		return fmt.Sprintf(constants.GRAPH_REASON_TAG_INTEREST, matchedTags[0])
	}

	if containsInt64(uf.PreferredSubCatIds, 0) {
		return fmt.Sprintf(constants.GRAPH_REASON_SUB_CATEGORY, subCategoryName)
	}

	return ""
}

// BuildRelations 构建图谱关系链列表
func BuildRelations(articleID, userID int64, tags string, uf *cache.UserGraphFeatures) []types.GraphRelation {
	var relations []types.GraphRelation
	if uf == nil || uf.IsEmpty() {
		return relations
	}

	if containsInt64(uf.FollowedAuthorIds, userID) {
		relations = append(relations, types.GraphRelation{
			Type:   constants.GRAPH_RELATION_TYPE_FOLLOW,
			Name:   "",
			Score:  0.25,
			Reason: constants.GRAPH_RELATION_FOLLOWED,
		})
	}

	matchedTags := intersectTags(tags, uf.TagList)
	for _, tag := range matchedTags {
		relations = append(relations, types.GraphRelation{
			Type:   constants.GRAPH_RELATION_TYPE_TAG,
			Name:   tag,
			Score:  0.07,
			Reason: constants.GRAPH_RELATION_TAG_INTEREST,
		})
	}

	return relations
}

func containsInt64(slice []int64, target int64) bool {
	for _, v := range slice {
		if v == target {
			return true
		}
	}
	return false
}

func intersectTags(artTags string, userTags []string) []string {
	var result []string
	artTagSet := make(map[string]struct{})
	for _, t := range strings.Split(artTags, ",") {
		t = strings.TrimSpace(t)
		if t != "" {
			artTagSet[t] = struct{}{}
		}
	}
	for _, ut := range userTags {
		if _, ok := artTagSet[ut]; ok {
			result = append(result, ut)
		}
	}
	return result
}
