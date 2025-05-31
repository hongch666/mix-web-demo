import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import yamlConfig from './config/yaml-config.service';
import { NacosModule } from './nacos/nacos.module';
import { ClientController } from './client/client.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserModule } from 'users/user.module';
import { User } from 'users/entity/user.entity';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'mysql', // 数据库类型
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'csc20040312',
      database: 'demo',
      entities: [User],
      synchronize: true,
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
