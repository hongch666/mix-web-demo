jest.mock("fs", () => ({
  promises: { readFile: jest.fn().mockResolvedValue(Buffer.from("template")) },
}));
jest.mock("docx-templates", () => ({
  createReport: jest.fn().mockResolvedValue(Buffer.from("docx")),
}));

import { WordService } from "./word.service";

describe("WordService", () => {
  // 验证模板和 HTML 内容会生成 Word 文件缓冲区
  it("验证模板内容生成 Word 缓冲区", async () => {
    await expect(
      new WordService().exportToWord(
        { content: "<p>正文</p>" },
        "template.docx",
      ),
    ).resolves.toEqual(Buffer.from("docx"));
  });
});
