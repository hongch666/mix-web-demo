/**
 * MySQL 数据库连接配置结构，供 TypeOrmModule 异步初始化读取
 */
export interface DatabaseConfig {
  type: "mysql";
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  logging: boolean;
}

/**
 * MongoDB 数据库连接配置结构，供 MongooseModule 异步初始化读取
 */
export interface MongoDbConfig {
  host: string;
  port: number;
  username?: string;
  password?: string;
  dbName: string;
  logging: boolean;
}
