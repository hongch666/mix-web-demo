package search

import (
	"context"
	"encoding/json"

	"app/common/constants"

	"github.com/olivere/elastic/v7"
)

// buildSearchDSL 拼装 ES 查询请求体，内容与实际发出的 search body 保持一致
// 覆盖 query、from、size、sort、highlight 五部分，其余参数沿用客户端默认值
// 只在 DSL 日志开关开启时调用，避免每次搜索都做一次序列化开销
func buildSearchDSL(query elastic.Query, from, size int, sortByCreateAt bool, highlight *elastic.Highlight) (string, error) {
	querySource, err := query.Source()
	if err != nil {
		return "", err
	}

	body := map[string]interface{}{
		"query":         querySource,
		"from":          from,
		"size":          size,
		"request_cache": true,
	}

	// 无关键词时只有过滤条件，_score 恒为 0，实际请求会带创建时间倒序，这里同步体现
	if sortByCreateAt {
		body["sort"] = []interface{}{
			map[string]interface{}{"create_at": map[string]interface{}{"order": "desc"}},
		}
	}

	if highlight != nil {
		highlightSource, highlightErr := highlight.Source()
		if highlightErr != nil {
			return "", highlightErr
		}
		body["highlight"] = highlightSource
	}

	raw, err := json.Marshal(body)
	if err != nil {
		return "", err
	}

	return string(raw), nil
}

// logSearchDSL 按开关输出 ES 查询 DSL，便于排查召回条件与打分脚本问题
// 开关关闭时直接返回，既不构造 DSL 也不产生日志
func (m *searchModel) logSearchDSL(ctx context.Context, query elastic.Query, from, size int, sortByCreateAt bool, highlight *elastic.Highlight) {
	if !m.dslLogEnabled || m.logger == nil {
		return
	}

	dsl, err := buildSearchDSL(query, from, size, sortByCreateAt, highlight)
	if err != nil {
		m.logger.Errorf(constants.ES_DSL_BUILD_FAIL, err)
		return
	}

	m.logger.WithContext(ctx).Infof(constants.ES_SEARCH_DSL_LOG, articlesIndexName, dsl)
}
