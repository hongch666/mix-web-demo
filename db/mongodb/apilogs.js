const apiLogsName = 'apilogs';
if (!mongoDb.getCollectionNames().includes(apiLogsName)) {
  mongoDb.createCollection(apiLogsName);
}
const apiLogs = mongoDb.getCollection(apiLogsName);
apiLogs.createIndex({ userId: 1, createdAt: -1 }, { name: 'userId_1_createdAt_-1' });
apiLogs.createIndex({ createdAt: -1 }, { name: 'createdAt_-1' });
apiLogs.createIndex({ apiPath: 1, createdAt: -1 }, { name: 'apiPath_1_createdAt_-1' });
apiLogs.createIndex(
  { userId: 1, apiMethod: 1, createdAt: -1 },
  { name: 'userId_1_apiMethod_1_createdAt_-1' },
);
