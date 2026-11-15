const logDeletionsName = 'logdeletions';
if (!mongoDb.getCollectionNames().includes(logDeletionsName)) {
  mongoDb.createCollection(logDeletionsName);
}
const logDeletions = mongoDb.getCollection(logDeletionsName);
// 同一日志重复删除只保留一条墓碑，数仓按主键删除天然幂等
logDeletions.createIndex(
  { eventId: 1, logType: 1 },
  { name: 'eventId_1_logType_1', unique: true },
);
// 墓碑只服务于删除向数仓的传播，90 天后由 TTL 自动回收，数仓残留由保留期清理兜底
logDeletions.createIndex(
  { createdAt: 1 },
  { name: 'createdAt_ttl', expireAfterSeconds: 7776000 },
);
