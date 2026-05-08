const dbName = 'demo';
const collectionName = 'articlelogs';

const mongoDb = db.getSiblingDB(dbName);

if (!mongoDb.getCollectionNames().includes(collectionName)) {
  mongoDb.createCollection(collectionName);
}

const collection = mongoDb.getCollection(collectionName);

collection.createIndex({ createdAt: -1 }, { name: 'createdAt_-1' });
collection.createIndex({ userId: 1, createdAt: -1 }, { name: 'userId_1_createdAt_-1' });
collection.createIndex({ articleId: 1, createdAt: -1 }, { name: 'articleId_1_createdAt_-1' });
collection.createIndex({ action: 1, createdAt: -1 }, { name: 'action_1_createdAt_-1' });
collection.createIndex(
  { userId: 1, action: 1, articleId: 1 },
  { name: 'userId_1_action_1_articleId_1' },
);
