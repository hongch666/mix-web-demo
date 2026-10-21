import { Module } from "@nestjs/common";
import { ApiLogModule } from "./apiLog/apiLog.module";
import { ArticleLogModule } from "./articleLog/articleLog.module";
import { DownloadModule } from "./download/download.module";
import { MongoToolsModule } from "./mongoTools/mongoTools.module";
import { SqlToolsModule } from "./sqlTools/sqlTools.module";
import { TableSettingsModule } from "./tableSettings/tableSettings.module";
import { TestModule } from "./test/test.module";
import { UploadModule } from "./upload/upload.module";

/**
 * 系统模块，聚合日志、下载、上传、表格列设置与数据库工具等子系统模块并统一导出
 */
@Module({
  imports: [
    TestModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    MongoToolsModule,
    UploadModule,
    TableSettingsModule,
    SqlToolsModule,
  ],
  exports: [
    ArticleLogModule,
    ApiLogModule,
    MongoToolsModule,
    DownloadModule,
    UploadModule,
    TableSettingsModule,
    SqlToolsModule,
  ],
})
export class SystemModule {}
