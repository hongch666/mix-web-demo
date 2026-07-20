import { Module } from "@nestjs/common";
import { MongooseModule } from "@nestjs/mongoose";
import { ArticleModule } from "src/module/system/article/article.module";
import { NacosModule } from "src/module/common/nacos/nacos.module";
import { UserModule } from "src/module/system/user/user.module";
import { LogConsumerService } from "./articleLog.consume.service";
import { ArticleLogController } from "./articleLog.controller";
import { ArticleLogService } from "./articleLog.service";
import { ArticleLog, ArticleLogSchema } from "./schema/articleLog.schema";

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ArticleLog.name, schema: ArticleLogSchema },
    ]),
    UserModule,
    ArticleModule,
    NacosModule,
  ],
  providers: [ArticleLogService, LogConsumerService],
  controllers: [ArticleLogController],
  exports: [ArticleLogService],
})
export class ArticleLogModule {}
