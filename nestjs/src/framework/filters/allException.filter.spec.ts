import { ArgumentsHost } from "@nestjs/common";
import { BusinessException } from "src/common/exceptions/business.exception";
import { AllExceptionsFilter } from "./allException.filter";

describe("AllExceptionsFilter异常过滤器", () => {
  // 验证业务异常会转换为统一的错误响应
  it("验证业务异常转换为统一响应", () => {
    const response = { status: jest.fn().mockReturnThis(), send: jest.fn() };
    const host = {
      switchToHttp: () => ({
        getResponse: () => response,
        getRequest: () => ({ method: "GET", url: "/test" }),
      }),
    } as unknown as ArgumentsHost;
    const logger = { error: jest.fn() };
    new AllExceptionsFilter(logger as never).catch(
      new BusinessException("参数错误", 422),
      host,
    );
    expect(response.status).toHaveBeenCalledWith(422);
    expect(response.send).toHaveBeenCalled();
  });
});
