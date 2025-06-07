import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import yamlConfig from './config/yaml-config.service';
import { NacosModule } from './nacos/nacos.module';
import { ClientController } from './client/client.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ArticleLogModule } from './log/log.module';
import { MongooseModule } from '@nestjs/mongoose';

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
          entities: db.entities,
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
    ArticleLogModule,
    NacosModule,
  ],
  controllers: [ClientController],
  providers: [],
})
export class AppModule {}
