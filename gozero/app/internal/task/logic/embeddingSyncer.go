package logic

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"app/common/constants"
	"app/internal/svc"
	"app/model/articles"

	_ "github.com/lib/pq"
)

// SyncEmbeddingToES 从 pgvector 读取每篇文章的 chunk 向量均值 → ES _update embedding_vector
func SyncEmbeddingToES(ctx context.Context, svcCtx *svc.ServiceContext) error {
	if svcCtx.ESClient == nil {
		return fmt.Errorf(constants.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
	}

	pgCfg := svcCtx.Config.Pgvector
	dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		pgCfg.Host, pgCfg.Port, pgCfg.Username, pgCfg.Password, pgCfg.Dbname)

	pgConn, err := sql.Open("postgres", dsn)
	if err != nil {
		return fmt.Errorf(constants.TASK_EMBEDDING_SYNC_CONNECT_FAIL, err)
	}
	defer pgConn.Close()

	var articleIDs []int64
	err = svcCtx.ArticlesModel.IteratePublishedArticles(ctx, 500, func(batch []articles.Articles) error {
		for _, a := range batch {
			articleIDs = append(articleIDs, a.Id)
		}
		return nil
	})
	if err != nil {
		return fmt.Errorf(constants.TASK_EMBEDDING_SYNC_ARTICLES_FAIL, err)
	}

	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(constants.TASK_EMBEDDING_SYNC_START_LOG, len(articleIDs)))
	}

	successCount, skipCount := 0, 0
	for _, articleID := range articleIDs {
		avgVec, err := averageChunkVectors(ctx, pgConn, articleID)
		if err != nil {
			svcCtx.Logger.Warning(fmt.Sprintf(constants.TASK_EMBEDDING_SYNC_PGVECTOR_FAIL, articleID, err))
			skipCount++
			continue
		}
		if avgVec == nil {
			skipCount++
			continue
		}

		_, err = svcCtx.ESClient.Update().
			Index("articles").
			Id(fmt.Sprintf("%d", articleID)).
			Doc(map[string]interface{}{"embedding_vector": avgVec}).
			RetryOnConflict(3).
			Do(ctx)
		if err != nil {
			svcCtx.Logger.Warning(fmt.Sprintf(constants.TASK_EMBEDDING_SYNC_ES_FAIL, articleID, err))
			skipCount++
			continue
		}
		successCount++
	}

	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(constants.TASK_EMBEDDING_SYNC_DONE_LOG, successCount, skipCount))
	}
	return nil
}

func averageChunkVectors(ctx context.Context, pgConn *sql.DB, articleID int64) ([]float64, error) {
	rows, err := pgConn.QueryContext(ctx, constants.PGVECTOR_AVERAGE_CHUNKS_QUERY,
		fmt.Sprintf("%d", articleID))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var allVectors [][]float64
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			continue
		}
		var vec []float64
		if err := json.Unmarshal([]byte(raw), &vec); err != nil {
			continue
		}
		allVectors = append(allVectors, vec)
	}

	if len(allVectors) == 0 {
		return nil, nil
	}

	dim := len(allVectors[0])
	avg := make([]float64, dim)
	for _, vec := range allVectors {
		for i := range vec {
			avg[i] += vec[i]
		}
	}
	count := float64(len(allVectors))
	for i := range avg {
		avg[i] /= count
	}
	return avg, nil
}
