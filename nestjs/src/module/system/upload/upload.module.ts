import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { OssModule } from "src/module/common/oss/oss.module";
import { UploadController } from "./upload.controller";
import { UploadService } from "./upload.service";

/**
 * 文件上传模块，注册上传的控制器与服务
 */
@Module({
  imports: [ConfigModule, OssModule],
  controllers: [UploadController],
  providers: [UploadService],
})
export class UploadModule {}
