const articleLogsName = 'articlelogs';
if (!mongoDb.getCollectionNames().includes(articleLogsName)) {
  mongoDb.createCollection(articleLogsName);
}
const articleLogs = mongoDb.getCollection(articleLogsName);
articleLogs.createIndex({ createdAt: -1 }, { name: 'createdAt_-1' });
articleLogs.createIndex({ userId: 1, createdAt: -1 }, { name: 'userId_1_createdAt_-1' });
articleLogs.createIndex({ articleId: 1, createdAt: -1 }, { name: 'articleId_1_createdAt_-1' });
articleLogs.createIndex({ action: 1, createdAt: -1 }, { name: 'action_1_createdAt_-1' });
// 搜索历史/浏览分布：userId + action 过滤后按时间倒序聚合，createdAt 必须在索引里才能免内存排序
articleLogs.createIndex(
  { userId: 1, action: 1, createdAt: -1 },
  { name: 'userId_1_action_1_createdAt_-1' },
);
// userId 与 articleId 同时过滤时按时间倒序取最近记录
articleLogs.createIndex(
  { userId: 1, articleId: 1, createdAt: -1 },
  { name: 'userId_1_articleId_1_createdAt_-1' },
);
