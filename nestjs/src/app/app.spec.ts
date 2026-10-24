import {
  AmqpConnection,
  AmqpConnectionManager,
} from "@golevelup/nestjs-rabbitmq";
import { getConnectionToken } from "@nestjs/mongoose";
import { Test } from "@nestjs/testing";
import { getDataSourceToken } from "@nestjs/typeorm";

// uuid@14 为 ESM-only 包，jest-runtime 的 CJS require 无法加载（生产 Node 20.19+ 与 Bun 均支持），冒烟测试只关心 DI 图解析，与 uuid 的真实实现无关，这里按单测规范在工厂中提供被用到的成员
jest.mock("uuid", () => ({ v4: () => "mocked-uuid" }));

import { RedisKeys } from "src/common/constants";
import { LoggerService } from "src/module/common/logger/logger.service";
import { InternalTokenUtil } from "../common/utils/internalToken.util";
import { AppModule } from "./app.module";

/**
 * 万能 noop 代理：任意属性访问与方法调用都返回自身
 *
 * 基础设施 provider 的工厂在 compile 阶段就会执行（TypeORM 还会重试 10 次、每次 3 秒），
 * 用它可以替换数据源与 Mongo 连接：既保留完整 DI 图校验，又不建立真实连接、不残留句柄。
 * then 返回 undefined，保证被 await 时不会被当成 thenable 卡住
 */
const noop: unknown = new Proxy(
  function noopFn(): unknown {
    return noop;
  },
  {
    get: (_target: unknown, property: string | symbol): unknown =>
      property === "then" ? undefined : noop,
  },
);

const mongooseConnectionStub = {
  models: {} as Record<string, unknown>,
  model: (): unknown => noop,
  close: async (): Promise<void> => undefined,
};

/**
 * RabbitMQ 连接管理器桩：RabbitMQModule 的工厂在编译阶段就会建立真实连接，
 * 连接超时 10s 且失败后持续重连，替换后不产生 socket、不残留句柄
 * 只提供 RabbitMQModule 自身用到的成员，不放行任意属性访问
 */
const amqpConnectionManagerStub = {
  getConnections: (): unknown[] => [],
  close: async (): Promise<void> => undefined,
  clearConnections: (): void => undefined,
};

/**
 * RabbitMQ 连接桩：ApiLogInterceptor 注入它并在请求完成后 publish 接口日志，
 * 显式提供该成员，冒烟测试不走请求流故不会真正调用
 */
const amqpConnectionStub = {
  publish: async (): Promise<boolean> => true,
};

/**
 * AppModule 冒烟测试
 *
 * 模块未 import、Provider 未导出等依赖装配错误只有 Nest 解析整个 DI 图时才会暴露，
 * TypeScript 编译与函数级单测都无法发现，此处通过编译完整根模块兜底
 */
describe("AppModule 冒烟测试", () => {
  it("AppModule 应能完成整个依赖图的解析", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(getDataSourceToken())
      .useValue(noop)
      .overrideProvider(getConnectionToken())
      .useValue(mongooseConnectionStub)
      .overrideProvider(RedisKeys.REDIS_CLIENT)
      .useValue(null)
      .overrideProvider(AmqpConnectionManager)
      .useValue(amqpConnectionManagerStub)
      .overrideProvider(AmqpConnection)
      .useValue(amqpConnectionStub)
      .compile();

    try {
      // 关键基础设施 Provider 可获取，说明全部模块的依赖装配成功
      expect(moduleRef.get(LoggerService)).toBeDefined();
      expect(moduleRef.get(InternalTokenUtil)).toBeDefined();
    } finally {
      await moduleRef.close();
    }
  });
});
