import { MiddlewareConsumer, Module, RequestMethod } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { APP_GUARD, APP_INTERCEPTOR } from '@nestjs/core';
import { MongooseModule } from '@nestjs/mongoose';
import { ScheduleModule } from '@nestjs/schedule';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ClsModule } from 'nestjs-cls';
import { InternalTokenGuard } from 'src/framework/guards/internalToken.guard';
import { RequireAdminGuard } from 'src/framework/guards/requireAdmin.guard';
import { ApiLogInterceptor } from 'src/framework/interceptors/apiLog.interceptor';
import { ApiModule } from '../api/api.module';
import yamlConfig from '../common/config/yamlConfig.service';
import { InternalTokenUtil } from '../common/utils/internalToken.util';
import { ClsMiddleware } from '../framework/middleware/cls.middleware';
import { ModulesModule } from '../modules/modules.module';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService): any => {
        const db: Record<string, unknown> = configService.get(
          'database',
        ) as Record<string, unknown>;
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
      useFactory: async (configService: ConfigService): Promise<any> => {
        const mongodb: Record<string, unknown> = configService.get(
          'mongodb',
        ) as Record<string, unknown>;
        const host: string = mongodb.host as string;
        const port: number = mongodb.port as number;
        const username: string = mongodb.username as string;
        const password: string = mongodb.password as string;
        const dbName: string = mongodb.dbName as string;

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
