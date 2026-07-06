import { Module } from "@nestjs/common";
import { ArticleModule } from "./article/article.module";
import { NacosModule } from "./nacos/nacos.module";
import { OssModule } from "./oss/oss.module";
import { TaskModule } from "./task/task.module";
import { UserModule } from "./user/user.module";
import { WordModule } from "./word/word.module";

@Module({
  imports: [
    ArticleModule,
    UserModule,
    NacosModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
  exports: [
    ArticleModule,
    UserModule,
    NacosModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
})
export class CommonModule {}
