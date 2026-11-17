import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { OssModule } from "src/module/common/oss/oss.module";
import { OssObjectModule } from "src/module/system/ossObject/ossObject.module";
import { UploadController } from "./upload.controller";
import { UploadService } from "./upload.service";

/**
 * 文件上传模块，注册上传控制器与服务，并依赖 OSS 对象模块登记上传记录
 */
@Module({
  imports: [ConfigModule, OssModule, OssObjectModule],
  controllers: [UploadController],
  providers: [UploadService],
  exports: [UploadService],
})
export class UploadModule {}
