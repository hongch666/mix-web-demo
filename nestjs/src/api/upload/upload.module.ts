import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { UploadController } from './upload.controller';
import { UploadService } from './upload.service';
import { OssModule } from 'src/modules/oss/oss.module';

@Module({
  imports: [ConfigModule, OssModule],
  controllers: [UploadController],
  providers: [UploadService],
})
export class UploadModule {}
