package service

import (
	"context"
	"encoding/json"
	"gin_proj/api/mapper"
	"gin_proj/common/ctxkey"
	"gin_proj/config"
	"gin_proj/entity/dto"
	"gin_proj/entity/po"
)

func SearchArticles(ctx context.Context, searchDTO dto.ArticleSearchDTO) po.SearchResult {
	data, total := mapper.SearchArticle(ctx, searchDTO)
	// 读取用户id
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	// 发送消息
	msg := map[string]interface{}{
		"action":  "search",
		"user_id": userID,
		"content": searchDTO,
		"msg":     "发起了文章搜索",
	}
	// 2. 转成 JSON 字符串
	jsonBytes, err := json.Marshal(msg)
	if err != nil {
		panic(err.Error())
	}
	// 3. 发送消息
	err = config.RabbitMQ.Send("log-queue", string(jsonBytes))
	if err != nil {
		panic(err.Error())
	}
	return po.SearchResult{
		Total: total,
		List:  data,
	}

}
