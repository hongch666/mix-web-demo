import { Module } from "@nestjs/common";
import { ClientModule } from "src/module/common/client";
import { NacosModule } from "src/module/common/nacos";
import { OssModule } from "src/module/common/oss";
import { WordModule } from "src/module/common/word";
import { DownloadController } from "./download.controller";
import { DownloadService } from "./download.service";

/**
 * 下载模块，注册文章导出下载的控制器与服务
 */
@Module({
  imports: [ClientModule, WordModule, NacosModule, OssModule],
  controllers: [DownloadController],
  providers: [DownloadService],
})
export class DownloadModule {}
