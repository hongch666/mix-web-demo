import { Module } from "@nestjs/common";
import { ClientModule } from "src/module/common/client/client.module";
import { NacosModule } from "src/module/common/nacos/nacos.module";
import { OssModule } from "src/module/common/oss/oss.module";
import { WordModule } from "src/module/common/word/word.module";
import { DownloadController } from "./download.controller";
import { DownloadService } from "./download.service";

@Module({
  imports: [ClientModule, WordModule, NacosModule, OssModule],
  controllers: [DownloadController],
  providers: [DownloadService],
})
export class DownloadModule {}
