package constants

// MQ 队列名 — 跨服务消息队列，生产方与消费方必须保持一致
const (
	// ===== 日志队列 =====

	// API 请求日志队列，gozero 与 fastapi 生产、nestjs 攒批落库 MongoDB
	API_LOG_QUEUE = "api-log-queue"
	// 文章操作日志队列，gozero 生产、nestjs 攒批落库 MongoDB
	ARTICLE_LOG_QUEUE = "article-log-queue"
)
