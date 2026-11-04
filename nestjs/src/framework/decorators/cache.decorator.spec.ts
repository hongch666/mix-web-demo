import "reflect-metadata";
import {
  CACHE_EVICT_KEY,
  CACHEABLE_KEY,
  CacheEvict,
  Cacheable,
  CacheableOptions,
  CacheEvictOptions,
} from "./cache.decorator";

/**
 * 取原型方法的函数引用，避免直接引用未绑定方法触发 lint 规则
 */
function prototypeMethod(prototype: object, name: string): object {
  return Object.getOwnPropertyDescriptor(prototype, name)?.value as object;
}

describe("缓存注解", () => {
  // 注解只写元数据，方法本身保持原样，缓存逻辑由 CacheExplorer 织入
  it("Cacheable 只写入元数据且不改变原方法", async () => {
    class DemoService {
      @Cacheable({
        key: (userId: number): string => `user:${userId}`,
        cacheNull: true,
      })
      async load(userId: number): Promise<number> {
        return userId;
      }
    }

    const metadata: CacheableOptions = Reflect.getMetadata(
      CACHEABLE_KEY,
      prototypeMethod(DemoService.prototype, "load"),
    ) as CacheableOptions;
    expect(typeof metadata.key).toBe("function");
    expect(metadata.cacheNull).toBe(true);
    await expect(new DemoService().load(7)).resolves.toBe(7);
  });

  // 失效注解只记录 key 生成规则，供执行器在方法成功后删除缓存
  it("CacheEvict 只写入元数据", () => {
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

    const metadata: CacheEvictOptions = Reflect.getMetadata(
      CACHE_EVICT_KEY,
      prototypeMethod(DemoService.prototype, "save"),
    ) as CacheEvictOptions;
    expect(Array.isArray(metadata.keys)).toBe(true);
    expect((metadata.keys as unknown[]).length).toBe(2);
  });

  // 两类注解使用不同的元数据键，互不覆盖
  it("两类注解写入不同的元数据键", () => {
    class DemoService {
      @Cacheable({ key: "query" })
      async load(): Promise<number> {
        return 1;
      }

      @CacheEvict({ keys: "query" })
      async save(): Promise<void> {
        return;
      }
    }

    const loadRef: object = prototypeMethod(DemoService.prototype, "load");
    const saveRef: object = prototypeMethod(DemoService.prototype, "save");
    expect(CACHEABLE_KEY).not.toBe(CACHE_EVICT_KEY);
    expect(Reflect.getMetadata(CACHEABLE_KEY, loadRef)).toBeDefined();
    expect(Reflect.getMetadata(CACHE_EVICT_KEY, loadRef)).toBeUndefined();
    expect(Reflect.getMetadata(CACHE_EVICT_KEY, saveRef)).toBeDefined();
  });
});
