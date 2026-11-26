import { Module } from "@nestjs/common";
import { NacosModule } from "src/module/common/nacos";
import { SpringClientService } from "./springClient.service";

/**
 * 客户端模块，装配并导出基于 Nacos 服务发现的 Spring 服务调用客户端
 */
@Module({
  imports: [NacosModule],
  providers: [SpringClientService],
  exports: [SpringClientService],
})
export class ClientModule {}
