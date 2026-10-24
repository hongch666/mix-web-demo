import { ApiProperty } from "@nestjs/swagger";
import { IsNotEmpty, IsString } from "class-validator";
import { ExposeName } from "src/common/utils/snakeCase";

/**
 * 文件上传结果结构，包含原始文件名、OSS 文件名与访问链接
 */
export interface UploadResult {
  originalFilename: string;
  ossFilename: string;
  ossUrl: string;
}

/**
 * 通过本地文件路径上传文件到 OSS 的请求DTO，含本地路径与 OSS 目标路径
 */
export class UploadDto {
  @ApiProperty({
    description: "本地文件路径（必须是服务本地存在的文件）",
    example: "/tmp/test.docx",
  })
  @ExposeName()
  @IsString({ message: "本地文件路径必须是字符串" })
  @IsNotEmpty({ message: "本地文件路径不能为空" })
  localFile!: string;

  @ApiProperty({
    description: "上传到 OSS 的目标路径（如 articles/test.docx）",
    example: "articles/test.docx",
  })
  @ExposeName()
  @IsString({ message: "OSS目标路径必须是字符串" })
  @IsNotEmpty({ message: "OSS目标路径不能为空" })
  ossFile!: string;
}
