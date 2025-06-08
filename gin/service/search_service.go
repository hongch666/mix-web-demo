package service

import (
	"context"
	"encoding/json"
	"gin_proj/config"
	"gin_proj/dto"
	"gin_proj/mapper"
	"gin_proj/po"
)

func SearchArticles(ctx context.Context, searchDTO dto.ArticleSearchDTO) (po.SearchResult, error) {
	data, total, err := mapper.SearchArticle(ctx, searchDTO)
	if err != nil {
		return po.SearchResult{}, err
	}
	// 发送消息
	msg := map[string]interface{}{
		"action":  "search",
		"user_id": 1, // TODO:从ctx中提取真实用户ID
		"content": searchDTO,
		"msg":     "发起了文章搜索",
	}
	// 2. 转成 JSON 字符串
	jsonBytes, err := json.Marshal(msg)
	if err != nil {
		return po.SearchResult{}, err
	}
	// 3. 发送消息
	err = config.RabbitMQ.Send("log-queue", string(jsonBytes))
	if err != nil {
		return po.SearchResult{}, err
	}
	return po.SearchResult{
		Total: total,
		List:  data,
	}, nil

}
