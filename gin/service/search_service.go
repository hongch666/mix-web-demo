package service

import (
	"context"
	"gin_proj/dto"
	"gin_proj/mapper"
	"gin_proj/po"
)

func SearchArticles(ctx context.Context, searchDTO dto.ArticleSearchDTO) (po.SearchResult, error) {
	data, total, err := mapper.SearchArticle(ctx, searchDTO)
	if err != nil {
		return po.SearchResult{}, err
	}
	return po.SearchResult{
		Total: total,
		List:  data,
	}, nil

}
