import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { TypeOrmModule } from "@nestjs/typeorm";
import { ClientModule } from "src/module/common/client/client.module";
import { NacosModule } from "src/module/common/nacos/nacos.module";
import { OssModule } from "src/module/common/oss/oss.module";
import { OssObject } from "./entities/ossObject.entity";
import { OssObjectService } from "./ossObject.service";

/**
 * OSS 对象模块，独立承载 OSS 对象账本与清理能力，供上传模块登记、定时任务调用清理
 */
@Module({
  imports: [
    ConfigModule,
    OssModule,
    ClientModule,
    NacosModule,
    TypeOrmModule.forFeature([OssObject]),
  ],
  providers: [OssObjectService],
  exports: [OssObjectService],
})
export class OssObjectModule {}
