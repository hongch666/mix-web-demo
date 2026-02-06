import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { createReport } from 'docx-templates';
import { htmlToText } from 'html-to-text';

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
    const absTemplatePath: string = path.isAbsolute(templatePath)
      ? templatePath
      : path.resolve(__dirname, '../../', templatePath);
    const template: Buffer = fs.readFileSync(absTemplatePath);

    // 这里将content转为docx可用的rawXml
    const processedData: Record<string, any> = {
      ...data,
      // 这里简单转为纯文本，保留html标签需用插件
      content: htmlToText(data.content || '', { wordwrap: false }),
    };

    const buffer: any = await createReport({
      template,
      data: processedData,
      cmdDelimiter: ['${', '}'],
    });

    return Buffer.from(buffer);
  }
}
