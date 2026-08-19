import { Module } from "@nestjs/common";
import { ApiLogModule } from "./apiLog/apiLog.module";
import { ArticleModule } from "./article/article.module";
import { ArticleLogModule } from "./articleLog/articleLog.module";
import { DownloadModule } from "./download/download.module";
import { MongoToolsModule } from "./mongoTools/mongoTools.module";
import { TableSettingsModule } from "./tableSettings/tableSettings.module";
import { TestModule } from "./test/test.module";
import { UploadModule } from "./upload/upload.module";
import { UserModule } from "./user/user.module";

@Module({
  imports: [
    TestModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    MongoToolsModule,
    ArticleModule,
    UserModule,
    UploadModule,
    TableSettingsModule,
  ],
  exports: [
    UserModule,
    ArticleModule,
    ArticleLogModule,
    ApiLogModule,
    MongoToolsModule,
    DownloadModule,
    UploadModule,
    TableSettingsModule,
  ],
})
export class SystemModule {}
