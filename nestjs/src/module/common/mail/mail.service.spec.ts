import { MailService } from "./mail.service";

describe("MailService", () => {
  // 验证邮件配置缺失时发送验证码会失败并记录警告
  it("验证缺少配置时拒绝发送验证码", async () => {
    const logger = { warning: jest.fn(), info: jest.fn(), error: jest.fn() };
    const service = new MailService(
      { get: jest.fn() } as never,
      logger as never,
    );
    await expect(
      service.sendVerificationCode({
        email: "user@example.com",
        code: "123456",
        type: "login",
      }),
    ).rejects.toThrow();
    expect(logger.warning).toHaveBeenCalled();
  });
});
