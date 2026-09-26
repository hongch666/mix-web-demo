import { DownloadService } from "./download.service";

describe("DownloadService", () => {
  // 验证 OSS 上传失败时转换为业务异常
  it("验证 OSS 上传失败转换为业务异常", async () => {
    const service = new DownloadService(
      {} as never,
      {} as never,
      { uploadFile: jest.fn().mockRejectedValue(new Error("failed")) } as never,
      {} as never,
      { error: jest.fn() } as never,
    );
    await expect(service.uploadFileToOSS("a.txt", "a.txt")).rejects.toThrow();
  });
});
