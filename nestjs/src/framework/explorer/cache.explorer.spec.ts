// uuid 为 ESM-only 包，缓存服务经 RedisService 间接引入，本测试用不到其实现，按单测规范在工厂中提供被用到的成员
jest.mock("uuid", () => ({ v4: () => "mocked-uuid" }));

import { DiscoveryService, MetadataScanner, Reflector } from "@nestjs/core";
import {
  Cacheable,
  CacheEvict,
} from "src/framework/decorators/cache.decorator";
import { LoggerService } from "src/module/common/logger/logger.service";
import { CacheExplorer } from "./cache.explorer";
import { CacheService } from "src/module/common/cache/cache.service";

describe("CacheExplorer", () => {
  const cache = {
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
    deleteMany: jest.fn(),
  };
  const cacheService = cache as unknown as CacheService;
  const loggerStub = {
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  };
  const logger = loggerStub as unknown as LoggerService;

  /**
   * 用给定实例模拟启动期扫描 Provider，返回执行器便于重复触发
   */
  function createExplorer(instances: object[]): CacheExplorer {
    const discovery = {
      getProviders: () => instances.map((instance) => ({ instance })),
    } as unknown as DiscoveryService;
    return new CacheExplorer(
      discovery,
      new MetadataScanner(),
      new Reflector(),
      cacheService,
      logger,
    );
  }

  /**
   * 织入注解后返回原实例，方法调用走包装后的实现
   */
  function wrap<T extends object>(service: T): T {
    createExplorer([service]).onModuleInit();
    return service;
  }

  beforeEach(() => {
    jest.clearAllMocks();
    cache.set.mockResolvedValue(undefined);
    cache.deleteMany.mockResolvedValue(undefined);
  });

  it("命中缓存时直接返回缓存值且不执行原方法", async () => {
    const loader = jest.fn().mockResolvedValue({ id: 7 });
    class DemoService {
      @Cacheable({ key: (userId: number): string => `user:${userId}` })
      async load(userId: number): Promise<{ id: number }> {
        return loader(userId) as { id: number };
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockResolvedValueOnce({ id: 7 });

    await expect(service.load(7)).resolves.toEqual({ id: 7 });
    expect(cache.get).toHaveBeenCalledWith("user:7");
    expect(loader).not.toHaveBeenCalled();
  });

  it("未命中时执行原方法并按注解配置回填缓存", async () => {
    const loader = jest.fn().mockResolvedValue({ id: 7 });
    class DemoService {
      @Cacheable({
        key: (userId: number): string => `user:${userId}`,
        localTtl: 30,
        redisTtl: 600,
      })
      async load(userId: number): Promise<{ id: number }> {
        return loader(userId) as { id: number };
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockResolvedValue(undefined);

    await expect(service.load(7)).resolves.toEqual({ id: 7 });
    expect(loader).toHaveBeenCalledWith(7);
    expect(cache.set).toHaveBeenCalledWith(
      "user:7",
      { id: 7 },
      { localTtl: 30, redisTtl: 600 },
    );
  });

  it("同一 key 并发未命中时只回源一次", async () => {
    const loader = jest.fn().mockResolvedValue({ id: 7 });
    class DemoService {
      @Cacheable({ key: "user:7" })
      async load(): Promise<{ id: number }> {
        return loader() as { id: number };
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockResolvedValue(undefined);

    const [first, second] = await Promise.all([service.load(), service.load()]);
    expect(loader).toHaveBeenCalledTimes(1);
    expect(first).toEqual({ id: 7 });
    expect(second).toEqual({ id: 7 });
  });

  it("未开启 cacheNull 时不缓存 null 结果", async () => {
    class DemoService {
      @Cacheable({ key: "user:1" })
      async load(): Promise<null> {
        return null;
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockResolvedValue(undefined);

    await expect(service.load()).resolves.toBeNull();
    expect(cache.set).not.toHaveBeenCalled();
  });

  it("开启 cacheNull 后缓存 null 结果", async () => {
    class DemoService {
      @Cacheable({ key: "user:1", cacheNull: true })
      async load(): Promise<null> {
        return null;
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockResolvedValue(undefined);

    await service.load();
    expect(cache.set).toHaveBeenCalledWith("user:1", null, {
      localTtl: undefined,
      redisTtl: undefined,
    });
  });

  it("key 生成函数返回空串时跳过缓存直接执行原方法", async () => {
    const loader = jest.fn().mockResolvedValue(1);
    class DemoService {
      @Cacheable({
        key: (userId?: number): string => (userId ? `user:${userId}` : ""),
      })
      async load(userId?: number): Promise<number> {
        return loader(userId) as number;
      }
    }

    const service = wrap(new DemoService());

    await expect(service.load()).resolves.toBe(1);
    expect(cache.get).not.toHaveBeenCalled();
    expect(cache.set).not.toHaveBeenCalled();
  });

  it("读取缓存异常时降级为直接回源", async () => {
    const loader = jest.fn().mockResolvedValue({ id: 7 });
    class DemoService {
      @Cacheable({ key: "user:7" })
      async load(): Promise<{ id: number }> {
        return loader() as { id: number };
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockRejectedValueOnce(new Error("cache read down"));

    await expect(service.load()).resolves.toEqual({ id: 7 });
    expect(loader).toHaveBeenCalledTimes(1);
    expect(loggerStub.warning).toHaveBeenCalled();
  });

  it("写入缓存异常时不影响业务返回", async () => {
    const loader = jest.fn().mockResolvedValue({ id: 7 });
    class DemoService {
      @Cacheable({ key: "user:7" })
      async load(): Promise<{ id: number }> {
        return loader() as { id: number };
      }
    }

    const service = wrap(new DemoService());
    cache.get.mockResolvedValue(undefined);
    cache.set.mockRejectedValueOnce(new Error("cache write down"));

    await expect(service.load()).resolves.toEqual({ id: 7 });
    expect(loggerStub.warning).toHaveBeenCalled();
  });

  it("原方法执行成功后失效注解声明的全部 key", async () => {
    class DemoService {
      @CacheEvict<[number, string]>({
        keys: [
          (userId: number): string => `user:${userId}`,
          (userId: number, tableKey: string): string =>
            `user:${userId}:${tableKey}`,
        ],
      })
      async save(userId: number, tableKey: string): Promise<void> {
        void userId;
        void tableKey;
      }
    }

    const service = wrap(new DemoService());

    await service.save(7, "articles");
    expect(cache.deleteMany).toHaveBeenCalledWith([
      "user:7",
      "user:7:articles",
    ]);
  });

  it("原方法抛错时不失效缓存", async () => {
    class DemoService {
      @CacheEvict({ keys: "user:7" })
      async save(): Promise<void> {
        throw new Error("save failed");
      }
    }

    const service = wrap(new DemoService());

    await expect(service.save()).rejects.toThrow("save failed");
    expect(cache.deleteMany).not.toHaveBeenCalled();
  });

  it("失效缓存异常时不把故障抛给业务调用方", async () => {
    class DemoService {
      @CacheEvict({ keys: "user:7" })
      async save(): Promise<void> {
        return;
      }
    }

    const service = wrap(new DemoService());
    cache.deleteMany.mockRejectedValueOnce(new Error("cache evict down"));

    await expect(service.save()).resolves.toBeUndefined();
    expect(loggerStub.warning).toHaveBeenCalled();
  });

  it("重复执行扫描不会重复织入同一个方法", async () => {
    const loader = jest.fn().mockResolvedValue(1);
    class DemoService {
      @Cacheable({ key: "user:1" })
      async load(): Promise<number> {
        return loader() as number;
      }
    }

    const service = new DemoService();
    const explorer = createExplorer([service]);
    explorer.onModuleInit();
    explorer.onModuleInit();
    cache.get.mockResolvedValue(undefined);

    await service.load();
    expect(cache.get).toHaveBeenCalledTimes(1);
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it("没有缓存注解的方法保持原样", async () => {
    class DemoService {
      async plain(): Promise<number> {
        return 1;
      }
    }

    const service = wrap(new DemoService());

    await expect(service.plain()).resolves.toBe(1);
    expect(Object.prototype.hasOwnProperty.call(service, "plain")).toBe(false);
    expect(cache.get).not.toHaveBeenCalled();
  });
});
