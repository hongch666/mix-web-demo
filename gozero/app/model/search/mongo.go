package search

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson"
)

func (m *searchModel) GetSearchHistory(ctx context.Context, userID int64) ([]string, error) {
	if m.mongoClient == nil {
		return nil, ErrNilMongoClient
	}
	if m.mongoDatabase == "" {
		return nil, ErrEmptyMongoDB
	}

	collection := m.mongoClient.Database(m.mongoDatabase).Collection(searchHistoryTableName)

	pipeline := []bson.M{
		{
			"$match": bson.M{
				"userId": userID,
				"action": "search",
			},
		},
		{
			"$sort": bson.M{
				"createdAt": -1,
			},
		},
		{
			"$addFields": bson.M{
				"keyword": "$content.Keyword",
			},
		},
		{
			"$match": bson.M{
				"keyword": bson.M{
					"$exists": true,
					"$nin":    []any{nil, ""},
				},
			},
		},
		{
			"$group": bson.M{
				"_id":       "$keyword",
				"createdAt": bson.M{"$first": "$createdAt"},
			},
		},
		{
			"$sort": bson.M{
				"createdAt": -1,
			},
		},
		{
			"$limit": 10,
		},
		{
			"$project": bson.M{
				"_id":       0,
				"keyword":   "$_id",
				"createdAt": 1,
			},
		},
	}

	cursor, err := collection.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	keywords := make([]string, 0)
	for cursor.Next(ctx) {
		var result struct {
			Keyword   string    `bson:"keyword"`
			CreatedAt time.Time `bson:"createdAt"`
		}
		if err = cursor.Decode(&result); err != nil {
			continue
		}
		keywords = append(keywords, result.Keyword)
	}

	return keywords, nil
}
