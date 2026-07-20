import { Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { NacosModule } from "src/module/common/nacos/nacos.module";
import { WordModule } from "src/module/common/word/word.module";
import { User } from "./entities/user.entity";
import { UserService } from "./user.service";

@Module({
  imports: [TypeOrmModule.forFeature([User]), WordModule, NacosModule],
  controllers: [],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}
