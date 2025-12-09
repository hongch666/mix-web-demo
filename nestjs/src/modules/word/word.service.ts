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
    const absTemplatePath = path.isAbsolute(templatePath)
      ? templatePath
      : path.resolve(__dirname, '../../', templatePath);
    const template = fs.readFileSync(absTemplatePath);

    // docx-templates 默认不支持html渲染，需要在模板中用rawXml插入html片段
    // 这里将content(html)转为docx可用的rawXml（简单处理：转纯文本，复杂需求需用docxtemplater-html-module等插件）
    // 如需保留格式，建议后续引入docxtemplater-html-module
    const processedData = {
      ...data,
      // 这里简单转为纯文本，保留html标签需用插件
      content: htmlToText(data.content || '', { wordwrap: false }),
    };

    const buffer = await createReport({
      template,
      data: processedData,
      cmdDelimiter: ['${', '}'],
    });

    return Buffer.from(buffer);
  }
}
