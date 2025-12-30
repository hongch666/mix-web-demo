import { Module } from '@nestjs/common';
import { NacosService } from './nacos.service';

@Module({
  providers: [
    NacosService
  ],
  exports: [
    NacosService
  ],
})
export class NacosModule {}
