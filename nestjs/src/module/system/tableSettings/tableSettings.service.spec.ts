/* eslint-disable @typescript-eslint/no-explicit-any */

// uuid 为 ESM-only 包，缓存服务经 RedisService 间接引入，本测试用不到其实现，按单测规范在工厂中提供被用到的成员
jest.mock("uuid", () => ({ v4: () => "mocked-uuid" }));

import { DiscoveryService, MetadataScanner, Reflector } from "@nestjs/core";
import { CacheExplorer } from "src/module/common/cache/cache.explorer";
import { CacheService } from "src/module/common/cache/cache.service";
import { LoggerService } from "src/module/common/logger/logger.service";
import { TableSettingsService } from "./tableSettings.service";

describe("TableSettingsService", () => {
  const store = new Map<string, unknown>();
  const cache = {
    get: jest.fn(async (key: string): Promise<unknown> => store.get(key)),
    set: jest.fn(async (key: string, value: unknown): Promise<void> => {
      store.set(key, value);
    }),
    delete: jest.fn(async (key: string): Promise<void> => {
      store.delete(key);
    }),
    deleteMany: jest.fn(async (keys: string[]): Promise<void> => {
      keys.forEach((key: string): boolean => store.delete(key));
    }),
  };

  /**
   * 构造服务实例并用执行器织入注解，等价于应用启动时的缓存包装
   */
  function createService(repository: any, logger: any): TableSettingsService {
    const service = new TableSettingsService(repository, logger);
    const discovery = {
      getProviders: () => [{ instance: service }],
    } as unknown as DiscoveryService;
    new CacheExplorer(
      discovery,
      new MetadataScanner(),
      new Reflector(),
      cache as unknown as CacheService,
      { warning: jest.fn() } as unknown as LoggerService,
    ).onModuleInit();
    return service;
  }

  beforeEach(() => {
    store.clear();
    jest.clearAllMocks();
  });

  it("保存新列设置时写库并失效单页与整用户的缓存", async () => {
    const repository = {
      findOne: jest.fn().mockResolvedValue(null),
      create: jest.fn((value) => value),
      save: jest
        .fn()
        .mockResolvedValue({ user_id: 7, table_key: "articles", columns: [] }),
    };
    const service = createService(repository, { info: jest.fn() });

    await expect(service.saveSettings(7, "articles", [])).resolves.toEqual({
      user_id: 7,
      table_key: "articles",
      columns: [],
    });
    expect(repository.create).toHaveBeenCalled();
    expect(cache.deleteMany).toHaveBeenCalledWith([
      "table:settings:7:articles",
      "table:settings:7:all",
    ]);
  });

  it("删除列设置时执行删除并失效对应缓存", async () => {
    const repository = { delete: jest.fn().mockResolvedValue({ affected: 1 }) };
    const logger = { info: jest.fn() };
    await createService(repository, logger).deleteSettings(7, "articles");
    expect(repository.delete).toHaveBeenCalledWith({
      user_id: 7,
      table_key: "articles",
    });
    expect(logger.info).toHaveBeenCalled();
    expect(cache.deleteMany).toHaveBeenCalledWith([
      "table:settings:7:articles",
      "table:settings:7:all",
    ]);
  });

  it("首次查询回填缓存，重复查询不再访问数据库", async () => {
    const repository = {
      findOne: jest
        .fn()
        .mockResolvedValue({ user_id: 7, table_key: "articles", columns: [] }),
    };
    const service = createService(repository, { info: jest.fn() });

    await service.getSettings(7, "articles");
    await service.getSettings(7, "articles");

    expect(repository.findOne).toHaveBeenCalledTimes(1);
    expect(cache.set).toHaveBeenCalledWith(
      "table:settings:7:articles",
      { user_id: 7, table_key: "articles", columns: [] },
      { localTtl: undefined, redisTtl: undefined },
    );
  });

  it("查询无结果时缓存 null，避免同一页面反复穿透", async () => {
    const repository = { findOne: jest.fn().mockResolvedValue(null) };
    const service = createService(repository, { info: jest.fn() });

    await expect(service.getSettings(7, "empty")).resolves.toBeNull();
    await expect(service.getSettings(7, "empty")).resolves.toBeNull();

    expect(repository.findOne).toHaveBeenCalledTimes(1);
    expect(cache.set).toHaveBeenCalledWith("table:settings:7:empty", null, {
      localTtl: undefined,
      redisTtl: undefined,
    });
  });
});
