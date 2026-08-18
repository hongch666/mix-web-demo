import { Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { TableSettings } from "./entities/tableSettings.entity";
import { TableSettingsController } from "./tableSettings.controller";
import { TableSettingsService } from "./tableSettings.service";

@Module({
  imports: [TypeOrmModule.forFeature([TableSettings])],
  controllers: [TableSettingsController],
  providers: [TableSettingsService],
  exports: [TableSettingsService],
})
export class TableSettingsModule {}
