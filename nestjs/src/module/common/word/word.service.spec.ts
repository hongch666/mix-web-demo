import * as fs from "node:fs";

import { WordService } from "./word.service";

jest.mock("docx-templates", () => ({
  createReport: jest.fn().mockResolvedValue(Buffer.from("docx")),
}));

describe("WordService", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 验证模板和 HTML 内容会生成 Word 文件缓冲区
  it("验证模板内容生成 Word 缓冲区", async () => {
    // 只替换读取模板这一个系统边界，避免 mock 整个 fs 模块污染其它测试文件的模块实例
    jest
      .spyOn(fs.promises, "readFile")
      .mockResolvedValue(Buffer.from("template"));

    await expect(
      new WordService().exportToWord(
        { content: "<p>正文</p>" },
        "template.docx",
      ),
    ).resolves.toEqual(Buffer.from("docx"));
  });
});
