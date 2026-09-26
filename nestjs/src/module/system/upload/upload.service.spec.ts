import { UploadService } from "./upload.service";

describe("UploadService", () => {
  // 验证本地文件上传会委托给 OSS 服务
  it("验证本地文件上传委托给 OSS", async () => {
    const uploadFile = jest.fn().mockResolvedValue("https://oss/file");
    const service = new UploadService(
      { uploadFile } as never,
      {} as never,
      {} as never,
    );
    await expect(service.uploadFile("local.txt", "remote.txt")).resolves.toBe(
      "https://oss/file",
    );
    expect(uploadFile).toHaveBeenCalledWith("local.txt", "remote.txt");
  });

  // 验证上传非 PDF 文件时返回参数错误
  it("验证非 PDF 文件被拒绝", async () => {
    const service = new UploadService(
      {} as never,
      {} as never,
      { info: jest.fn() } as never,
    );
    await expect(
      service.uploadPdf({ filename: "image.png" }),
    ).rejects.toThrow();
  });
});
