import { Module } from "@nestjs/common";
import { WordService } from "./word.service";

/**
 * Word 文档导出模块，提供并导出基于模板生成 Word 文档的 WordService
 */
@Module({
  providers: [WordService],
  exports: [WordService],
})
export class WordModule {}
