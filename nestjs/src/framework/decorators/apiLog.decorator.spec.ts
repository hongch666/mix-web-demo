/* eslint-disable @typescript-eslint/unbound-method */

import "reflect-metadata";
import { ApiLog, API_LOG_KEY } from "./apiLog.decorator";

describe("ApiLog装饰器", () => {
  // 验证字符串参数会转换为完整的日志配置
  it("验证字符串参数转换为日志配置", () => {
    class Fixture {
      @ApiLog("查询记录")
      list(): void {}
    }
    expect(Reflect.getMetadata(API_LOG_KEY, Fixture.prototype.list)).toEqual({
      message: "查询记录",
      includeParams: true,
      logLevel: "info",
    });
  });
});
