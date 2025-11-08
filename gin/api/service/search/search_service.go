package search

import (
	"context"
	"encoding/json"
	"gin_proj/api/mapper"
	"gin_proj/common/ctxkey"
	"gin_proj/config"
	"gin_proj/entity/dto"
	"gin_proj/entity/vo"
)

type SearchService struct{}

func (s *SearchService) SearchArticles(ctx context.Context, searchDTO dto.ArticleSearchDTO) vo.SearchVO {
	// mapper注入
	searchMapper := mapper.Group.SearchMapper
	data, total := searchMapper.SearchArticle(ctx, searchDTO)
	// 读取用户id
	userID, _ := ctx.Value(ctxkey.UserIDKey).(int64)
	// 如果搜索关键字为空，就不发送消息
	if searchDTO.Keyword != "" {
		// 发送消息
		msg := map[string]interface{}{
			"action":  "search",
			"user_id": userID,
			"content": searchDTO,
			"msg":     "发起了文章搜索",
		}
		// 转成 JSON 字符串
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			panic(err.Error())
		}
		// 发送消息
		err = config.RabbitMQ.Send("log-queue", string(jsonBytes))
		if err != nil {
			panic(err.Error())
		}
	}
	return vo.SearchVO{
		Total: total,
		List:  data,
	}

}

// GetSearchHistory 获取用户搜索历史关键词（最近10条）
func (s *SearchService) GetSearchHistory(ctx context.Context, userID int64) ([]string, error) {
	// mapper注入
	searchMapper := mapper.Group.SearchMapper
	keywords, err := searchMapper.GetSearchHistory(ctx, userID)
	if err != nil {
		return nil, err
	}
	return keywords, nil
}
