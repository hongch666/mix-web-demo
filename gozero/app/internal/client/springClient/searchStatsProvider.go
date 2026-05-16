package springClient

import (
	"context"

	"app/model/search"
)

type SearchStatsProvider struct {
	client *SpringClient
}

func NewSearchStatsProvider(client *SpringClient) *SearchStatsProvider {
	return &SearchStatsProvider{client: client}
}

func (p *SearchStatsProvider) GetSearchStats(ctx context.Context, articleIDs []int64) (map[int64]search.ArticleStats, error) {
	remoteStats, err := p.client.GetArticleSearchStats(ctx, articleIDs)
	if err != nil {
		return nil, err
	}
	stats := make(map[int64]search.ArticleStats, len(remoteStats))
	for id, stat := range remoteStats {
		stats[id] = search.ArticleStats{
			Views:             stat.Views,
			LikeCount:         stat.LikeCount,
			CollectCount:      stat.CollectCount,
			AuthorFollowCount: stat.AuthorFollowCount,
		}
	}
	return stats, nil
}
