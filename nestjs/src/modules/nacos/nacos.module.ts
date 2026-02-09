import { Module } from '@nestjs/common';
import { NacosService } from './nacos.service';
import { InternalTokenUtil } from '../../common/utils/internal-token.util';

@Module({
  providers: [NacosService, InternalTokenUtil],
  exports: [NacosService, InternalTokenUtil],
})
export class NacosModule {}
