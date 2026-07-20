import { Module } from "@nestjs/common";
import { NacosModule } from "../nacos/nacos.module";
import { SpringClientService } from "./springClient.service";

@Module({
  imports: [NacosModule],
  providers: [SpringClientService],
  exports: [SpringClientService],
})
export class ClientModule {}
