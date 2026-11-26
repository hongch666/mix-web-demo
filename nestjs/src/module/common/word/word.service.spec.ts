import * as fs from "node:fs";
import * as path from "node:path";
import { WordService } from "./word.service";

jest.mock("docx-templates", () => ({
  createReport: jest.fn().mockResolvedValue(Buffer.from("docx")),
}));

describe("WordService", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 验证模板可读时使用配置路径生成 Word 缓冲区
  it("验证配置的模板可读时生成 Word 缓冲区", async () => {
    // 只替换文件系统这一个系统边界，避免 mock 整个 fs 模块污染其它测试文件
    jest.spyOn(fs.promises, "access").mockResolvedValue(undefined);
    const readFile = jest
      .spyOn(fs.promises, "readFile")
      .mockResolvedValue(Buffer.from("template"));

    await expect(
      new WordService().exportToWord(
        { content: "<p>正文</p>" },
        "word/template.docx",
      ),
    ).resolves.toEqual(Buffer.from("docx"));

    expect(readFile).toHaveBeenCalledWith(
      path.resolve(process.cwd(), "word/template.docx"),
    );
  });

  // 验证配置路径不存在时回退镜像内置模板，避免部署目录不一致导致导出失败
  it("验证配置的模板缺失时回退内置模板", async () => {
    jest
      .spyOn(fs.promises, "access")
      .mockRejectedValueOnce(new Error("ENOENT"))
      .mockResolvedValue(undefined);
    const readFile = jest
      .spyOn(fs.promises, "readFile")
      .mockResolvedValue(Buffer.from("builtin"));

    await expect(
      new WordService().exportToWord(
        { content: "<p>正文</p>" },
        "../static/word/template.docx",
      ),
    ).resolves.toEqual(Buffer.from("docx"));

    // 断言实际读取的是内置模板，正则同时兼容 Windows 与 Linux 的路径分隔符
    expect(readFile).toHaveBeenCalledWith(
      expect.stringMatching(/assets[\\/]word[\\/]template\.docx$/),
    );
  });

  // 验证配置路径与内置模板都不可读时抛出带尝试路径的业务异常
  it("验证模板全部缺失时抛出业务异常", async () => {
    jest.spyOn(fs.promises, "access").mockRejectedValue(new Error("ENOENT"));

    await expect(
      new WordService().exportToWord({ content: "" }, "word/template.docx"),
    ).rejects.toThrow("Word 模板文件不存在");
  });
});
