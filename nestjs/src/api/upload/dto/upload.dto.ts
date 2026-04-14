import { ApiProperty } from "@nestjs/swagger";
import { IsNotEmpty, IsString, MinLength } from "class-validator";

export interface UploadResult {
  original_filename: string;
  oss_filename: string;
  oss_url: string;
}

export class UploadDto {
  @ApiProperty({
    description: "本地文件路径（必须是服务本地存在的文件）",
    example: "/tmp/test.docx",
  })
  @IsString({ message: "本地文件路径必须是字符串" })
  @IsNotEmpty({ message: "本地文件路径不能为空" })
  @MinLength(5, { message: "本地文件路径长度不能少于5个字符" })
  local_file!: string;

  @ApiProperty({
    description: "上传到 OSS 的目标路径（如 articles/test.docx）",
    example: "articles/test.docx",
  })
  @IsString({ message: "OSS目标路径必须是字符串" })
  @IsNotEmpty({ message: "OSS目标路径不能为空" })
  @MinLength(5, { message: "OSS目标路径长度不能少于5个字符" })
  oss_file!: string;
}
