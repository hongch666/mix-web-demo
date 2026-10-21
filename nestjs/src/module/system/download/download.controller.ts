import { Controller, Get, Param } from "@nestjs/common";
import { ApiOperation, ApiParam, ApiTags } from "@nestjs/swagger";
import {
  ApiResponseModel,
  SwaggerStringData,
} from "src/common/utils/swaggerResponse";
import { ApiResponse, success } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { DownloadService } from "./download.service";

/**
 * 文章导出下载接口，提供 Word、Markdown、PDF 三种格式的导出下载
 */
@Controller("download")
@ApiTags("下载模块")
export class DownloadController {
  constructor(private readonly downloadService: DownloadService) {}

  /**
   * 按文章 ID 导出 Word 文档并返回 OSS 下载链接
   */
  @Get("word/:id")
  @ApiOperation({
    summary: "下载文章Word",
    description: "通过id下载对应文章Word",
  })
  @ApiParam({ name: "id", type: "number", description: "文章ID" })
  @ApiLog("下载文章Word")
  @ApiResponseModel({ data: SwaggerStringData })
  async downloadWord(@Param("id") id: number): Promise<ApiResponse<string>> {
    const url: string = await this.downloadService.exportToWordAndSave(id);
    return success(url);
  }

  /**
   * 按文章 ID 导出 Markdown 文件并返回 OSS 下载链接
   */
  @Get("markdown/:id")
  @ApiOperation({
    summary: "下载文章Markdown",
    description: "通过id下载对应文章的Markdown并返回OSS链接",
  })
  @ApiParam({ name: "id", type: "number", description: "文章ID" })
  @ApiLog("下载文章Markdown")
  @ApiResponseModel({ data: SwaggerStringData })
  async downloadMarkdown(
    @Param("id") id: number,
  ): Promise<ApiResponse<string>> {
    const url: string = await this.downloadService.exportMarkdownAndUpload(
      Number(id),
    );
    return success(url);
  }

  /**
   * 按文章 ID 导出 PDF 文件并返回 OSS 下载链接
   */
  @Get("pdf/:id")
  @ApiOperation({
    summary: "下载文章PDF",
    description: "通过id下载对应文章的PDF并返回OSS链接",
  })
  @ApiParam({ name: "id", type: "number", description: "文章ID" })
  @ApiLog("下载文章PDF")
  @ApiResponseModel({ data: SwaggerStringData })
  async downloadPdf(@Param("id") id: number): Promise<ApiResponse<string>> {
    const url: string = await this.downloadService.exportToPdfAndSave(id);
    return success(url);
  }
}
