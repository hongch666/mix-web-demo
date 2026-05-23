import { MiddlewareConsumer, Module, RequestMethod } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { APP_GUARD, APP_INTERCEPTOR } from '@nestjs/core';
import { MongooseModule } from '@nestjs/mongoose';
import type { MongooseModuleOptions } from '@nestjs/mongoose';
import { ScheduleModule } from '@nestjs/schedule';
import { TypeOrmModule } from '@nestjs/typeorm';
import type { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { RabbitMQModule } from '@golevelup/nestjs-rabbitmq';
import { ClsModule } from 'nestjs-cls';
import { InternalTokenGuard } from 'src/framework/guards/internalToken.guard';
import { RequireAdminGuard } from 'src/framework/guards/requireAdmin.guard';
import { ApiLogInterceptor } from 'src/framework/interceptors/apiLog.interceptor';
import { ApiModule } from '../api/api.module';
import yamlConfig from '../common/config/yamlConfig.service';
import { InternalTokenUtil } from '../common/utils/internalToken.util';
import { ClsMiddleware } from '../framework/middleware/cls.middleware';
import { ModulesModule } from '../modules/modules.module';
import { RedisModule } from '../modules/redis/redis.module';

interface DatabaseConfig {
  type: 'mysql';
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  logging: boolean;
}

interface MongoDbConfig {
  host: string;
  port: number;
  username?: string;
  password?: string;
  dbName: string;
}

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService): TypeOrmModuleOptions => {
        const db: DatabaseConfig = configService.get<DatabaseConfig>(
          'database',
        )!;
        return {
          type: db.type,
          host: db.host,
          port: db.port,
          username: db.username,
          password: db.password,
          database: db.database,
          synchronize: false,
          logging: db.logging,
          autoLoadEntities: true,
        };
      },
    }),
    ConfigModule.forRoot({
      isGlobal: true,
      load: [yamlConfig],
    }),
    MongooseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: async (
        configService: ConfigService,
      ): Promise<MongooseModuleOptions> => {
        const mongodb: MongoDbConfig = configService.get<MongoDbConfig>(
          'mongodb',
        )!;
        const { host, port, username, password, dbName } = mongodb;

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
      inject: [ConfigService],
    }),
    ClsModule.forRoot({
      global: true,
      middleware: { mount: true },
    }),
    ScheduleModule.forRoot(),
    RedisModule.forRoot(),
    RabbitMQModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => {
        const host: string = configService.get<string>('rabbitmq.host')!;
        const port: number = configService.get<number>('rabbitmq.port')!;
        const username: string = configService.get<string>('rabbitmq.username')!;
        const password: string = configService.get<string>('rabbitmq.password')!;
        const vhost: string = configService.get<string>('rabbitmq.vhost')!;
        const uri: string = `amqp://${username}:${password}@${host}:${port}${vhost === '/' ? '' : `/${vhost}`}`;

        return {
          uri,
          exchanges: [],
          defaultRpcTimeout: 10000,
          defaultExchangeType: 'direct',
          connectionInitOptions: { timeout: 10000 },
          queues: [
            {
              name: 'api-log-queue',
              options: { durable: true },
            },
            {
              name: 'article-log-queue',
              options: { durable: true },
            },
          ],
        };
      },
    }),
    ApiModule,
    ModulesModule,
  ],
  controllers: [],
  providers: [
    InternalTokenUtil,
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
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(ClsMiddleware)
      .forRoutes({ path: '*', method: RequestMethod.ALL });
  }
}
