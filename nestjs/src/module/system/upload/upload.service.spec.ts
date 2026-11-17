import * as os from "node:os";
import { UploadService } from "./upload.service";

/**
 * 构造 UploadService 测试实例，OSS/账本/CLS 依赖全部用桩替换
 */
function buildService(
  overrides: {
    oss?: Record<string, unknown>;
    ledger?: Record<string, unknown>;
    cls?: Record<string, unknown>;
  } = {},
): UploadService {
  const oss = overrides.oss ?? { uploadFile: jest.fn() };
  const ledger = overrides.ledger ?? { register: jest.fn() };
  const cls = overrides.cls ?? { get: jest.fn() };
  const config = { get: jest.fn().mockReturnValue(os.tmpdir()) };
  return new UploadService(
    oss as never,
    config as never,
    { info: jest.fn(), error: jest.fn(), warning: jest.fn() } as never,
    ledger as never,
    cls as never,
  );
}

describe("UploadService", () => {
  // 验证本地文件上传委托给 OSS 并登记账本（内部来源）
  it("本地文件上传委托给 OSS 并登记 internal 来源", async () => {
    const uploadFile = jest.fn().mockResolvedValue("https://oss/file");
    const register = jest.fn().mockResolvedValue(true);
    const service = buildService({
      oss: { uploadFile },
      ledger: { register },
    });

    await expect(
      service.uploadFile("local.txt", "articles/remote.txt"),
    ).resolves.toBe("https://oss/file");
    expect(uploadFile).toHaveBeenCalledWith("local.txt", "articles/remote.txt");
    expect(register).toHaveBeenCalledWith(
      expect.objectContaining({
        ossKey: "articles/remote.txt",
        source: "internal",
        prefixType: "articles",
      }),
    );
  });

  // 验证上传非 PDF 文件时返回参数错误
  it("非 PDF 文件被拒绝", async () => {
    const service = buildService();
    await expect(
      service.uploadPdf({ filename: "image.png" }),
    ).rejects.toThrow();
  });

  // 验证登录后上传图片登记 user_image 来源并携带用户ID
  it("登录用户上传图片登记 user_image 与用户ID", async () => {
    const uploadFile = jest.fn().mockResolvedValue("https://oss/pic/a.png");
    const register = jest.fn().mockResolvedValue(true);
    const service = buildService({
      oss: { uploadFile, deleteObjects: jest.fn() },
      ledger: { register },
      cls: { get: jest.fn().mockReturnValue(42) },
    });
    const file = {
      filename: "a.png",
      toBuffer: jest.fn().mockResolvedValue(Buffer.from("img")),
    };

    await service.uploadImage(file);

    expect(register).toHaveBeenCalledWith(
      expect.objectContaining({ source: "user_image", uploaderUserId: 42 }),
    );
  });

  // 验证匿名上传图片登记 public_image 且不携带用户ID
  it("匿名上传图片登记 public_image 且用户ID为空", async () => {
    const uploadFile = jest.fn().mockResolvedValue("https://oss/pic/a.png");
    const register = jest.fn().mockResolvedValue(true);
    const service = buildService({
      oss: { uploadFile, deleteObjects: jest.fn() },
      ledger: { register },
      cls: { get: jest.fn().mockReturnValue(undefined) },
    });
    const file = {
      filename: "a.png",
      toBuffer: jest.fn().mockResolvedValue(Buffer.from("img")),
    };

    await service.uploadPublicImage(file);

    expect(register).toHaveBeenCalledWith(
      expect.objectContaining({ source: "public_image", uploaderUserId: null }),
    );
  });

  // 验证账本写入失败时回滚删除 OSS 对象并抛出异常
  it("账本写入失败时回滚删除 OSS 对象", async () => {
    const uploadFile = jest.fn().mockResolvedValue("https://oss/pic/a.png");
    const deleteObjects = jest.fn().mockResolvedValue(1);
    const register = jest.fn().mockRejectedValue(new Error("db down"));
    const service = buildService({
      oss: { uploadFile, deleteObjects },
      ledger: { register },
    });
    const file = {
      filename: "a.png",
      toBuffer: jest.fn().mockResolvedValue(Buffer.from("img")),
    };

    await expect(service.uploadImage(file)).rejects.toThrow();
    expect(deleteObjects).toHaveBeenCalledWith([
      expect.stringMatching(/^pic\//),
    ]);
  });

  // 验证 CLS 缺失时当前用户为 null，不抛异常
  it("CLS 上下文缺失时匿名上传仍可登记", async () => {
    const uploadFile = jest.fn().mockResolvedValue("https://oss/pic/a.png");
    const register = jest.fn().mockResolvedValue(true);
    const service = buildService({
      oss: { uploadFile, deleteObjects: jest.fn() },
      ledger: { register },
    });
    const file = {
      filename: "a.png",
      toBuffer: jest.fn().mockResolvedValue(Buffer.from("img")),
    };

    await service.uploadPublicImage(file);

    expect(register).toHaveBeenCalledWith(
      expect.objectContaining({ uploaderUserId: null }),
    );
  });
});
