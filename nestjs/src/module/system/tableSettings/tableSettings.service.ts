import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Messages, RedisKeys } from "src/common/constants";
import {
  Cacheable,
  CacheEvict,
} from "src/framework/decorators/cache.decorator";
import { LoggerService } from "src/module/common/logger/logger.service";
import { Repository } from "typeorm";
import { TableSettings } from "./entities/tableSettings.entity";

/**
 * 表格列设置服务，负责按用户与页面标识查询、保存与删除表格列配置
 * 查询走本地加 Redis 两级缓存，保存与删除后同时失效单页与整用户列表的缓存
 * L1 本地缓存按 TTL 过期，多实例部署时其它实例的本地缓存最多滞后一个 L1 TTL
 */
@Injectable()
export class TableSettingsService {
  constructor(
    @InjectRepository(TableSettings)
    private readonly tableSettingsRepository: Repository<TableSettings>,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 获取用户指定页面的列配置，空结果同样缓存以避免重复穿透
   */
  @Cacheable({
    key: (userId: number, tableKey: string): string =>
      RedisKeys.CACHE_TABLE_SETTINGS(userId, tableKey),
    cacheNull: true,
  })
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
  @Cacheable({
    key: (userId: number): string =>
      RedisKeys.CACHE_TABLE_SETTINGS_LIST(userId),
  })
  async getAllSettings(userId: number): Promise<TableSettings[]> {
    return this.tableSettingsRepository.find({
      where: { user_id: userId },
    });
  }

  /**
   * 保存（upsert）用户指定页面的列配置
   */
  @CacheEvict<[number, string, object]>({
    keys: [
      (userId: number, tableKey: string): string =>
        RedisKeys.CACHE_TABLE_SETTINGS(userId, tableKey),
      (userId: number): string => RedisKeys.CACHE_TABLE_SETTINGS_LIST(userId),
    ],
  })
  async saveSettings(
    userId: number,
    tableKey: string,
    columns: object,
  ): Promise<TableSettings> {
    // 直接读库而不是复用带缓存的 getSettings，避免拿本地旧值覆盖并发写入的结果
    const existing: TableSettings | null =
      await this.tableSettingsRepository.findOne({
        where: { user_id: userId, table_key: tableKey },
      });

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
  @CacheEvict<[number, string]>({
    keys: [
      (userId: number, tableKey: string): string =>
        RedisKeys.CACHE_TABLE_SETTINGS(userId, tableKey),
      (userId: number): string => RedisKeys.CACHE_TABLE_SETTINGS_LIST(userId),
    ],
  })
  async deleteSettings(userId: number, tableKey: string): Promise<void> {
    await this.tableSettingsRepository.delete({
      user_id: userId,
      table_key: tableKey,
    });
    this.logger.info(Messages.TABLE_SETTINGS_DELETED(userId, tableKey));
  }
}
