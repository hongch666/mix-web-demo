import { Module } from '@nestjs/common';
import { InternalTokenUtil } from '../../common/utils/internalToken.util';
import { NacosService } from './nacos.service';

@Module({
  providers: [NacosService, InternalTokenUtil],
  exports: [NacosService, InternalTokenUtil],
})
export class NacosModule {}
