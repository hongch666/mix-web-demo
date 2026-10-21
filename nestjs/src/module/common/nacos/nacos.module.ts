import { Module } from "@nestjs/common";
import { InternalTokenUtil } from "src/common/utils/internalToken.util";
import { NacosService } from "./nacos.service";

/**
 * Nacos 服务注册与发现模块，导出 NacosService 与内部令牌工具供其他模块调用
 */
@Module({
  providers: [NacosService, InternalTokenUtil],
  exports: [NacosService, InternalTokenUtil],
})
export class NacosModule {}
