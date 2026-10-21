import { RabbitMQConfig, RabbitMQModule } from "@golevelup/nestjs-rabbitmq";
import { MiddlewareConsumer, Module, RequestMethod } from "@nestjs/common";
import { ConfigModule, ConfigService } from "@nestjs/config";
import { APP_GUARD, APP_INTERCEPTOR } from "@nestjs/core";
import type { MongooseModuleOptions } from "@nestjs/mongoose";
import { MongooseModule } from "@nestjs/mongoose";
import { ScheduleModule } from "@nestjs/schedule";
import type { TypeOrmModuleOptions } from "@nestjs/typeorm";
import { TypeOrmModule } from "@nestjs/typeorm";
import mongoose from "mongoose";
import { ClsModule } from "nestjs-cls";
import config, { isTaskEnabled } from "src/config";
import { AllExceptionsFilter } from "src/framework/filters/allException.filter";
import { InternalTokenGuard } from "src/framework/guards/internalToken.guard";
import { RequireAdminGuard } from "src/framework/guards/requireAdmin.guard";
import { ApiLogInterceptor } from "src/framework/interceptors/apiLog.interceptor";
import { CommonModule } from "src/module/common/common.module";
import { LoggerService } from "src/module/common/logger/logger.service";
import { createMongooseDebugLogger } from "src/module/common/logger/mongooseDebugLogger";
import { RedisModule } from "src/module/common/redis/redis.module";
import { SystemModule } from "src/module/system/system.module";
import { InternalTokenUtil } from "../common/utils/internalToken.util";
import { ClsMiddleware } from "../framework/middleware/cls.middleware";

/**
 * MySQL 数据库连接配置结构，供 TypeOrmModule 异步初始化读取
 */
interface DatabaseConfig {
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
interface MongoDbConfig {
  host: string;
  port: number;
  username?: string;
  password?: string;
  dbName: string;
  logging: boolean;
}

/**
 * NestJS 根模块，聚合 TypeORM、Mongoose、Redis、RabbitMQ、CLS 等基础设施配置，并注册全局过滤器、拦截器与守卫
 */
@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService): TypeOrmModuleOptions => {
        const db: DatabaseConfig =
          configService.get<DatabaseConfig>("database.mysql")!;
        return {
          type: db.type,
          host: db.host,
          port: db.port,
          username: db.username,
          password: db.password,
          database: db.database,
          synchronize: true,
          logging: db.logging,
          autoLoadEntities: true,
        };
      },
    }),
    ConfigModule.forRoot({
      isGlobal: true,
      load: [(): Record<string, unknown> => config],
    }),
    MongooseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: async (
        configService: ConfigService,
        loggerService: LoggerService,
      ): Promise<MongooseModuleOptions> => {
        const mongodb: MongoDbConfig =
          configService.get<MongoDbConfig>("database.mongodb")!;
        const { host, port, username, password, dbName, logging } = mongodb;

        // 独立开关开启时把 mongoose 集合操作日志路由到统一日志服务
        // mongoose.set 是全局生效，本项目只有一个 mongo 连接，无隔离问题
        if (logging) {
          mongoose.set("debug", createMongooseDebugLogger(loggerService));
        }

        // 根据是否有用户名和密码构建 URI
        let uri: string;
        if (username && password) {
          uri = `mongodb://${username}:${password}@${host}:${port}`;
        } else {
          uri = `mongodb://${host}:${port}`;
        }

        return {
          uri,
          dbName,
          autoCreate: true,
        };
      },
      inject: [ConfigService, LoggerService],
    }),
    ClsModule.forRoot({
      global: true,
      middleware: { mount: true },
    }),
    // 定时任务开关关闭时不注册 ScheduleModule，@Cron 任务不再触发（改由 Dolphin 调度器触发 /task/* 接口）
    ...(isTaskEnabled(config) ? [ScheduleModule.forRoot()] : []),
    RedisModule.forRoot(),
    RabbitMQModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService): RabbitMQConfig => {
        const host: string = configService.get<string>("rabbitmq.host")!;
        const port: number = configService.get<number>("rabbitmq.port")!;
        const username: string =
          configService.get<string>("rabbitmq.username")!;
        const password: string =
          configService.get<string>("rabbitmq.password")!;
        const vhost: string = configService.get<string>("rabbitmq.vhost")!;
        const uri: string = `amqp://${username}:${password}@${host}:${port}${vhost === "/" ? "" : `/${vhost}`}`;

        return {
          uri,
          exchanges: [],
          defaultRpcTimeout: 10000,
          defaultExchangeType: "direct",
          connectionInitOptions: { timeout: 10000 },
          queues: [
            {
              name: "api-log-queue",
              options: { durable: true },
            },
            {
              name: "article-log-queue",
              options: { durable: true },
            },
          ],
        };
      },
    }),
    CommonModule,
    SystemModule,
  ],
  controllers: [],
  providers: [
    InternalTokenUtil,
    AllExceptionsFilter,
    {
      provide: APP_INTERCEPTOR,
      useClass: ApiLogInterceptor,
    },
    {
      provide: APP_GUARD,
      useClass: InternalTokenGuard,
    },
    {
      provide: APP_GUARD,
      useClass: RequireAdminGuard,
    },
  ],
})
export class AppModule {
  /**
   * 为所有路由注册 ClsMiddleware，建立请求级上下文
   */
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(ClsMiddleware)
      .forRoutes({ path: "*", method: RequestMethod.ALL });
  }
}
