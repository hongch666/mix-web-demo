import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Messages } from "src/common/constants";
import { LoggerService } from "src/module/common/logger/logger.service";
import { Repository } from "typeorm";
import { TableSettings } from "./entities/tableSettings.entity";

@Injectable()
export class TableSettingsService {
  constructor(
    @InjectRepository(TableSettings)
    private readonly tableSettingsRepository: Repository<TableSettings>,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 获取用户指定页面的列配置
   */
  async getSettings(
    userId: number,
    tableKey: string,
  ): Promise<TableSettings | null> {
    return this.tableSettingsRepository.findOne({
      where: { user_id: userId, table_key: tableKey },
    });
  }

  /**
   * 获取用户所有页面的列配置
   */
  async getAllSettings(userId: number): Promise<TableSettings[]> {
    return this.tableSettingsRepository.find({
      where: { user_id: userId },
    });
  }

  /**
   * 保存（upsert）用户指定页面的列配置
   */
  async saveSettings(
    userId: number,
    tableKey: string,
    columns: object,
  ): Promise<TableSettings> {
    const existing: TableSettings | null = await this.getSettings(
      userId,
      tableKey,
    );

    if (existing) {
      existing.columns = columns;
      const saved: TableSettings =
        await this.tableSettingsRepository.save(existing);
      this.logger.info(Messages.TABLE_SETTINGS_UPDATED(userId, tableKey));
      return saved;
    }

    const entity: TableSettings = this.tableSettingsRepository.create({
      user_id: userId,
      table_key: tableKey,
      columns,
    });
    const saved: TableSettings =
      await this.tableSettingsRepository.save(entity);
    this.logger.info(Messages.TABLE_SETTINGS_CREATED(userId, tableKey));
    return saved;
  }

  /**
   * 删除用户指定页面的列配置（恢复默认）
   */
  async deleteSettings(userId: number, tableKey: string): Promise<void> {
    await this.tableSettingsRepository.delete({
      user_id: userId,
      table_key: tableKey,
    });
    this.logger.info(Messages.TABLE_SETTINGS_DELETED(userId, tableKey));
  }
}
