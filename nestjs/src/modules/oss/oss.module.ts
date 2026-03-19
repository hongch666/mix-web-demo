import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { OssService } from './oss.service';

@Module({
  imports: [ConfigModule],
  providers: [OssService],
  exports: [OssService],
})
export class OssModule {}
