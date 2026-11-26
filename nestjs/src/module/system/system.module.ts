import { Module } from "@nestjs/common";
import { ApiLogModule } from "src/module/system/apiLog";
import { ArticleLogModule } from "src/module/system/articleLog";
import { DownloadModule } from "src/module/system/download";
import { LogDeletionModule } from "src/module/system/logDeletion";
import { MongoToolsModule } from "src/module/system/mongoTools";
import { SqlToolsModule } from "src/module/system/sqlTools";
import { TableSettingsModule } from "src/module/system/tableSettings";
import { TaskModule } from "src/module/system/task";
import { TestModule } from "src/module/system/test";
import { UploadModule } from "src/module/system/upload";

/**
 * 系统模块，聚合日志、下载、上传、定时任务、表格列设置与数据库工具等子系统模块并统一导出
 */
@Module({
  imports: [
    TestModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    LogDeletionModule,
    MongoToolsModule,
    UploadModule,
    TableSettingsModule,
    SqlToolsModule,
    TaskModule,
  ],
  exports: [
    ArticleLogModule,
    ApiLogModule,
    MongoToolsModule,
    DownloadModule,
    UploadModule,
    TableSettingsModule,
    SqlToolsModule,
    TaskModule,
  ],
})
export class SystemModule {}
