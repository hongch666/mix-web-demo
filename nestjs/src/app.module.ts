import { MiddlewareConsumer, Module, RequestMethod } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import yamlConfig from './config/yaml-config.service';
import { NacosModule } from './nacos/nacos.module';
import { ClientController } from './client/client.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ArticleLogModule } from './log/log.module';
import { MongooseModule } from '@nestjs/mongoose';
import { RabbitMQModule } from './mq/mq.module';
import { ArticleModule } from './article/article.module';
import { ClsModule } from 'nestjs-cls';
import { ClsMiddleware } from './middleware/cls.middleware';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => {
        const db = configService.get('database');
        return {
          type: db.type,
          host: db.host,
          port: db.port,
          username: db.username,
          password: db.password,
          database: db.database,
          synchronize: db.synchronize,
          logging: db.logging,
          entities: [__dirname + '/**/*.entity{.ts,.js}'],
        };
      },
    }),
    ConfigModule.forRoot({
      isGlobal: true,
      load: [yamlConfig],
    }),
    MongooseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        uri: configService.get<string>('mongodb.url'),
        dbName: configService.get<string>('mongodb.dbName'),
      }),
      inject: [ConfigService],
    }),
    ClsModule.forRoot({
      global: true,
      middleware: { mount: true },
    }),
    ArticleLogModule,
    NacosModule,
    RabbitMQModule,
    ArticleModule,
  ],
  controllers: [ClientController],
  providers: [],
})
export class AppModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(ClsMiddleware)
      .forRoutes({ path: '*', method: RequestMethod.ALL });
  }
}
