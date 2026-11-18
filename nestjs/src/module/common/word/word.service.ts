import { Injectable } from "@nestjs/common";
import { createReport } from "docx-templates";
import * as fs from "fs";
import { htmlToText } from "html-to-text";
import * as path from "path";
import { ErrorIds, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";

/** 模板文件名，调用方只传目录时自动补齐 */
const TEMPLATE_FILE_NAME = "template.docx";

/**
 * 内置模板路径：src 与 dist 下 module/common/word 的层级一致，向上三级即服务根目录
 */
const BUILTIN_TEMPLATE_PATH: string = path.resolve(
  __dirname,
  "../../../assets/word",
  TEMPLATE_FILE_NAME,
);

/**
 * Word 文档生成服务，使用 docx-templates 将数据填充到模板生成文档 Buffer
 */
@Injectable()
export class WordService {
  /**
   * 根据模板和数据生成 Word 文档 Buffer
   * @param data 需要填充到模板的数据对象
   * @param templatePath 模板文件路径（目录或 .docx 文件），缺失时回退到随包发布的内置模板
   */
  async exportToWord(
    data: Record<string, unknown>,
    templatePath?: string,
  ): Promise<Buffer> {
    const absTemplatePath: string =
      await this.resolveTemplatePath(templatePath);
    const template: Buffer = await fs.promises.readFile(absTemplatePath);

    // 这里将content转为docx可用的rawXml
    const processedData: Record<string, unknown> = {
      ...data,
      // 这里简单转为纯文本，保留html标签需用插件
      content: htmlToText((data.content as string) || "", { wordwrap: false }),
    };

    const buffer: unknown = await createReport({
      template,
      data: processedData,
      cmdDelimiter: ["${", "}"],
    });

    return Buffer.from(buffer as Buffer);
  }

  /**
   * 解析模板真实路径，优先使用配置路径，其次使用镜像内置模板
   * @param templatePath 配置的模板路径，可为绝对路径、相对当前工作目录的路径或目录
   */
  private async resolveTemplatePath(templatePath?: string): Promise<string> {
    const candidates: string[] = [];
    if (templatePath) {
      const configured: string = path.isAbsolute(templatePath)
        ? templatePath
        : path.resolve(process.cwd(), templatePath);
      candidates.push(
        path.extname(configured).toLowerCase() === ".docx"
          ? configured
          : path.join(configured, TEMPLATE_FILE_NAME),
      );
    }
    candidates.push(BUILTIN_TEMPLATE_PATH);

    for (const candidate of candidates) {
      if (await this.isReadable(candidate)) {
        return candidate;
      }
    }

    throw BusinessException.internalServerError(
      Messages.WORD_TEMPLATE_NOT_FOUND(candidates.join("、")),
      ErrorIds.WORD_TEMPLATE_NOT_FOUND,
    );
  }

  /**
   * 判断文件是否存在且可读
   * @param filePath 待检查的文件路径
   */
  private async isReadable(filePath: string): Promise<boolean> {
    try {
      await fs.promises.access(filePath, fs.constants.R_OK);
      return true;
    } catch {
      return false;
    }
  }
}
