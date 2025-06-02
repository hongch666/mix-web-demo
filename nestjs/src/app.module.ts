import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import yamlConfig from './config/yaml-config.service';
import { NacosModule } from './nacos/nacos.module';
import { ClientController } from './client/client.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserModule } from 'users/user.module';
import { User } from 'users/entity/user.entity';

@Module({
  imports: [
    /* TypeOrmModule.forRoot({
      type: 'mysql', // 数据库类型
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'csc20040312',
      database: 'demo',
      entities: [User],
      synchronize: true,
    }), */
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
    NacosModule,
    UserModule,
  ],
  controllers: [ClientController],
  providers: [],
})
export class AppModule {}
