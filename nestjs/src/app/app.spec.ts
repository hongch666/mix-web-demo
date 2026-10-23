import { Test } from "@nestjs/testing";

// uuid@14 为 ESM-only 包，jest-runtime 的 CJS require 无法加载（生产 Node 20.19+ 与 Bun 均支持），
// 冒烟测试只关心 DI 图解析，与 uuid 的真实实现无关，这里按单测规范在工厂中提供被用到的成员
jest.mock("uuid", () => ({ v4: () => "mocked-uuid" }));

import { LoggerService } from "src/module/common/logger/logger.service";
import { InternalTokenUtil } from "../common/utils/internalToken.util";
import { AppModule } from "./app.module";

/**
 * AppModule 冒烟测试
 *
 * 模块未 import、Provider 未导出等依赖装配错误只有 Nest 解析整个 DI 图时才会暴露，
 * TypeScript 编译与函数级单测都无法发现，此处通过编译完整根模块兜底。
 * 仅调用 compile()（不触发 onModuleInit/onApplicationBootstrap），
 * 因此不会真实连接 MySQL/RabbitMQ/Nacos
 */
describe("AppModule 冒烟测试", () => {
  it("AppModule 应能完成整个依赖图的解析", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    // 关键基础设施 Provider 可获取，说明全部模块的依赖装配成功
    expect(moduleRef.get(LoggerService)).toBeDefined();
    expect(moduleRef.get(InternalTokenUtil)).toBeDefined();
  });
});
