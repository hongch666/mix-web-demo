package service

import (
	"context"
	"encoding/json"
	"gin_proj/config"
	"gin_proj/ctxkey"
	"gin_proj/dto"
	"gin_proj/mapper"
	"gin_proj/po"
	"log"
)

func SearchArticles(ctx context.Context, searchDTO dto.ArticleSearchDTO) po.SearchResult {
	data, total := mapper.SearchArticle(ctx, searchDTO)
	// 读取用户id
	log.Println(ctx.Value(ctxkey.UsernameKey))
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
