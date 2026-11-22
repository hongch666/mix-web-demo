import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Repository } from "typeorm";
import { Defaults, Messages } from "src/common/constants";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { LoggerService } from "src/module/common/logger/logger.service";
import { NacosService } from "src/module/common/nacos/nacos.service";
import { OssObjectInfo, OssService } from "src/module/common/oss/oss.service";
import { OssObject } from "./entities/ossObject.entity";

/**
 * OSS 对象账本登记参数
 */
export interface OssObjectRecord {
  /** 对象 key（不含域名） */
  ossKey: string;
  /** 完整访问 URL */
  ossUrl: string;
  /** key 前缀类型 */
  prefixType: string;
  /** 上传来源 */
  source: string;
  /** 上传用户ID，匿名上传为 null */
  uploaderUserId?: number | null;
  /** 对象字节数 */
  fileSize?: number | null;
}

/**
 * OSS 清理结果统计
 */
export interface OssCleanupResult {
  /** 扫描到的在用引用数 */
  scanned: number;
  /** 补录的历史对象数 */
  backfilled: number;
  /** 删除的无引用对象数 */
  deleted: number;
  /** 处理失败数 */
  failed: number;
}

/**
 * OSS 对象服务，统一承载账本登记、历史补录、引用扫描与无主对象清理
 */
@Injectable()
export class OssObjectService {
  constructor(
    @InjectRepository(OssObject)
    private readonly repository: Repository<OssObject>,
    private readonly ossService: OssService,
    private readonly nacosService: NacosService,
    private readonly springClient: SpringClientService,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 登记一个 OSS 对象，唯一键冲突时忽略，返回是否为本服务新增
   */
  async register(record: OssObjectRecord): Promise<boolean> {
    const result = await this.repository
      .createQueryBuilder()
      .insert()
      .into(OssObject)
      .values({
        oss_key: record.ossKey,
        oss_url: record.ossUrl,
        prefix_type: record.prefixType,
        source: record.source,
        uploader_user_id: record.uploaderUserId ?? null,
        file_size: record.fileSize ?? null,
      })
      .orIgnore()
      .execute();
    // INSERT IGNORE 中被忽略的行不会生成 identifier，据此判断是否真正写入
    return result.generatedMaps.length > 0;
  }

  /**
   * 批量补录历史对象，唯一键冲突时忽略，返回实际补录条数
   */
  async backfill(records: OssObjectRecord[]): Promise<number> {
    if (records.length === 0) {
      return 0;
    }
    const now = new Date();
    const result = await this.repository
      .createQueryBuilder()
      .insert()
      .into(OssObject)
      .values(
        records.map((record) => ({
          oss_key: record.ossKey,
          oss_url: record.ossUrl,
          prefix_type: record.prefixType,
          source: record.source,
          uploader_user_id: record.uploaderUserId ?? null,
          file_size: record.fileSize ?? null,
          last_verified_at: now,
        })),
      )
      .orIgnore()
      .execute();
    return result.generatedMaps.length;
  }

  /**
   * 查询账本中全部对象 key
   */
  async listAllKeys(): Promise<string[]> {
    const rows = await this.repository
      .createQueryBuilder("obj")
      .select("obj.oss_key", "oss_key")
      .getRawMany<{ oss_key: string }>();
    return rows.map((row) => row.oss_key);
  }

  /**
   * 查询账本中在指定 key 前缀下、创建时间早于 cutoff 的对象 key，用于宽限期清理
   */
  async listKeysOlderThan(
    cutoff: Date,
    prefixes: readonly string[],
  ): Promise<string[]> {
    if (prefixes.length === 0) {
      return [];
    }
    const conditions: string[] = [];
    const parameters: Record<string, string> = {};
    prefixes.forEach((prefix, index) => {
      conditions.push(`obj.oss_key LIKE :prefix${index}`);
      parameters[`prefix${index}`] = `${prefix}%`;
    });
    const rows = await this.repository
      .createQueryBuilder("obj")
      .select("obj.oss_key", "oss_key")
      .where("obj.create_at < :cutoff", { cutoff })
      .andWhere(`(${conditions.join(" OR ")})`, parameters)
      .getRawMany<{ oss_key: string }>();
    return rows.map((row) => row.oss_key);
  }

  /**
   * 批量标记对象最近一次被扫描确认在用
   */
  async markVerified(keys: string[], verifiedAt: Date): Promise<void> {
    if (keys.length === 0) {
      return;
    }
    await this.repository
      .createQueryBuilder()
      .update(OssObject)
      .set({ last_verified_at: verifiedAt })
      .where("oss_key IN (:...keys)", { keys })
      .execute();
  }

  /**
   * 按 key 批量删除账本记录，返回实际删除条数
   */
  async removeByKeys(keys: string[]): Promise<number> {
    if (keys.length === 0) {
      return 0;
    }
    const result = await this.repository.delete(
      keys.map((key) => ({ oss_key: key })),
    );
    return result.affected ?? 0;
  }

  /**
   * 执行一轮完整清理；dryRun 为 true 时只统计不删除对象与账本
   */
  async cleanup(dryRun: boolean): Promise<OssCleanupResult> {
    const result: OssCleanupResult = {
      scanned: 0,
      backfilled: 0,
      deleted: 0,
      failed: 0,
    };

    // 阶段 1：收集在用引用快照（Spring 库 + 当前词云）
    const usedKeys: Set<string> = await this.collectUsedKeys(() => {
      result.failed += 1;
    });
    result.scanned = usedKeys.size;

    // 阶段 2：补录在用但账本确实缺失的历史对象
    const existingKeys: Set<string> = new Set(await this.listAllKeys());
    const toBackfill: OssObjectRecord[] = [...usedKeys]
      .filter((key) => !existingKeys.has(key))
      .map((key) => this.buildRecord(key, "backfill"));
    result.backfilled = await this.backfill(toBackfill);
    this.logger.info(Messages.OSS_CLEANUP_BACKFILLED(result.backfilled));
    for (const record of toBackfill) {
      existingKeys.add(record.ossKey);
    }

    // 任一在用引用来源查询失败时，usedKeys 不完整，跳过本轮删除避免误删（fail-closed）
    if (result.failed > 0) {
      this.logger.warning(Messages.OSS_CLEANUP_SKIP_DELETE_ON_PARTIAL_SCAN);
      return result;
    }

    // 阶段 3：清理账本中超过宽限期且已不在用的对象
    const cutoff: Date = new Date(Date.now() - Defaults.OSS_CLEANUP_GRACE_MS);
    const staleKeys: string[] = (
      await this.listKeysOlderThan(cutoff, Defaults.OSS_CLEANUP_KEY_PREFIXES)
    ).filter((key) => !usedKeys.has(key));
    const staleResult = await this.deleteKeys(staleKeys, dryRun, true);
    result.deleted += staleResult.deleted;
    result.failed += staleResult.failed;

    // 阶段 4：清理 OSS 里存在但账本中已无记录的对象
    const listed: OssObjectInfo[] = await this.ossService.listObjects("");
    // 宽限期同样作用于孤儿对象：导出下载产物刚上传就未登记账本，未满 1h 或时间未知的对象本轮不清理
    const orphanKeys: string[] = listed
      .filter((item) => this.ossService.isAllowedCleanupKey(item.name))
      .filter(
        (item) =>
          !existingKeys.has(item.name) &&
          item.lastModified !== undefined &&
          item.lastModified < cutoff.getTime(),
      )
      .map((item) => item.name);
    const orphanResult = await this.deleteKeys(orphanKeys, dryRun, false);
    result.deleted += orphanResult.deleted;
    result.failed += orphanResult.failed;

    this.logger.info(
      Messages.OSS_CLEANUP_COMPLETED(
        result.scanned,
        result.backfilled,
        result.deleted,
        result.failed,
      ),
    );
    return result;
  }

  /**
   * 收集数据库与缓存中在用的 OSS key 快照
   */
  private async collectUsedKeys(onFailure: () => void): Promise<Set<string>> {
    const keys = new Set<string>();

    // Spring 库里的头像与权威参考文本
    try {
      const response: Record<string, unknown> =
        await this.springClient.listOssReferenceUrls();
      const data: unknown = SpringClientService.extractData(response);
      if (Array.isArray(data)) {
        for (const item of data) {
          // Spring 返回原始链接，key 解析与非本 bucket 域名过滤统一在 NestJS 完成
          const key: string | null =
            typeof item === "string" ? this.ossService.extractKey(item) : null;
          if (key) {
            keys.add(key);
          }
        }
      }
    } catch (error: unknown) {
      this.logFailure(error);
      onFailure();
    }

    // FastAPI 当前词云 URL：缓存过期返回空，旧词云对象按无引用清理
    try {
      const response: Record<string, unknown> = await this.nacosService.call({
        serviceName: Defaults.FASTAPI_SERVICE_NAME,
        method: "GET",
        path: "/analyze/internal/wordcloud-url",
      });
      const url: unknown = SpringClientService.extractData(response);
      const key: string | null =
        typeof url === "string" ? this.ossService.extractKey(url) : null;
      if (key) {
        keys.add(key);
      }
    } catch (error: unknown) {
      this.logFailure(error);
      onFailure();
    }

    return keys;
  }

  /**
   * 记录引用查询或删除失败，不中断整轮清理
   */
  private logFailure(error: unknown): void {
    const message: string =
      error instanceof Error ? error.message : String(error);
    this.logger.error(Messages.OSS_CLEANUP_FAILED(message));
  }

  /**
   * 批量删除对象：先删 OSS，成功后按需删账本；dry-run 时仅统计不删除
   * 删除失败会计入 failed，避免任务日志显示"删除 0，失败 0"而掩盖删除环节异常
   */
  private async deleteKeys(
    keys: string[],
    dryRun: boolean,
    removeLedger: boolean,
  ): Promise<{ deleted: number; failed: number }> {
    if (keys.length === 0) {
      return { deleted: 0, failed: 0 };
    }
    if (dryRun) {
      return { deleted: keys.length, failed: 0 };
    }
    let deleted = 0;
    let failed = 0;
    for (const key of keys) {
      try {
        await this.ossService.deleteObjects([key]);
        if (removeLedger) {
          await this.removeByKeys([key]);
        }
        deleted += 1;
      } catch (error: unknown) {
        failed += 1;
        const message: string =
          error instanceof Error ? error.message : String(error);
        this.logger.error(Messages.OSS_CLEANUP_FAILED(message));
      }
    }
    return { deleted, failed };
  }

  /**
   * 由对象 key 构造账本记录
   */
  private buildRecord(key: string, source: string): OssObjectRecord {
    return {
      ossKey: key,
      ossUrl: this.ossService.getFileUrl(key),
      prefixType: key.split("/")[0] ?? key,
      source,
      uploaderUserId: null,
    };
  }
}
