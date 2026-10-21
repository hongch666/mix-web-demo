import { Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { TableSettings } from "./entities/tableSettings.entity";
import { TableSettingsController } from "./tableSettings.controller";
import { TableSettingsService } from "./tableSettings.service";

/**
 * 表格列设置模块，注册列设置的控制器与服务并导出服务
 */
@Module({
  imports: [TypeOrmModule.forFeature([TableSettings])],
  controllers: [TableSettingsController],
  providers: [TableSettingsService],
  exports: [TableSettingsService],
})
export class TableSettingsModule {}
