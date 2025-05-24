import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import yamlConfig from './config/yaml-config.service';
import { NacosModule } from './nacos/nacos.module';
import { ClientController } from './client/client.controller';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [yamlConfig],
    }),
    NacosModule],
  controllers: [ClientController],
  providers: [],
})
export class AppModule {}
