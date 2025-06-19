import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { createReport } from 'docx-templates';

@Injectable()
export class WordService {
  /**
   * 根据模板和数据生成 Word 文档 Buffer
   * @param data 需要填充到模板的数据对象
   * @param templatePath 模板文件的绝对路径或相对路径
   */
  async exportToWord(
    data: Record<string, any>,
    templatePath: string,
  ): Promise<Buffer> {
    // 读取模板文件
    const absTemplatePath = path.isAbsolute(templatePath)
      ? templatePath
      : path.resolve(__dirname, '../../', templatePath);
    const template = fs.readFileSync(absTemplatePath);

    // 使用 docx-templates 渲染数据到模板
    const buffer = await createReport({
      template,
      data,
      cmdDelimiter: ['${', '}'],
    });

    // 返回 Buffer，可用于文件下载
    return Buffer.from(buffer);
  }
}
