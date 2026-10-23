import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import { UploadDto } from "./upload.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

describe("UploadDto", () => {
  // 验证合法的上传请求通过校验，localFile、ossFile 带 @ExposeName，请求键名为 snake_case
  it("验证合法上传请求通过校验", async () => {
    const dto = (await pipe.transform(
      { local_file: "/tmp/test.docx", oss_file: "articles/test.docx" },
      { type: "body" as const, metatype: UploadDto },
    )) as UploadDto;

    expect(dto.localFile).toBe("/tmp/test.docx");
    expect(dto.ossFile).toBe("articles/test.docx");
  });

  // 验证本地文件路径为空被拒绝
  it("验证空本地文件路径被拒绝", async () => {
    await expect(
      pipe.transform(
        { local_file: "", oss_file: "articles/test.docx" },
        { type: "body" as const, metatype: UploadDto },
      ),
    ).rejects.toThrow();
  });

  // 验证OSS目标路径为空被拒绝
  it("验证空OSS目标路径被拒绝", async () => {
    await expect(
      pipe.transform(
        { local_file: "/tmp/test.docx", oss_file: "" },
        { type: "body" as const, metatype: UploadDto },
      ),
    ).rejects.toThrow();
  });

  // 验证OSS目标路径缺失被拒绝
  it("验证缺失OSS目标路径被拒绝", async () => {
    await expect(
      pipe.transform(
        { local_file: "/tmp/test.docx" },
        { type: "body" as const, metatype: UploadDto },
      ),
    ).rejects.toThrow();
  });

  // 验证数组输入无法隐式转换为字符串，被校验拒绝
  it("验证非字符串OSS目标路径被拒绝", async () => {
    await expect(
      pipe.transform(
        { local_file: "/tmp/test.docx", oss_file: ["articles/test.docx"] },
        { type: "body" as const, metatype: UploadDto },
      ),
    ).rejects.toThrow();
  });
});
