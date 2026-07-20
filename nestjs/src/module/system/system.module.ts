import { Module } from "@nestjs/common";
import { ApiLogModule } from "./apiLog/apiLog.module";
import { ArticleLogModule } from "./articleLog/articleLog.module";
import { ArticleModule } from "./article/article.module";
import { DownloadModule } from "./download/download.module";
import { TestModule } from "./test/test.module";
import { UploadModule } from "./upload/upload.module";
import { UserModule } from "./user/user.module";

@Module({
  imports: [
    TestModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    ArticleModule,
    UserModule,
    UploadModule,
  ],
})
export class SystemModule {}
