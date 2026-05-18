import { ApiProperty } from "@nestjs/swagger";
import { ExposeName } from "src/common/utils/snake-case.serializer";
import { IsNotEmpty, IsString, MinLength } from "class-validator";

export interface UploadResult {
  originalFilename: string;
  ossFilename: string;
  ossUrl: string;
}

export class UploadDto {
  @ApiProperty({
    description: "本地文件路径（必须是服务本地存在的文件）",
    example: "/tmp/test.docx",
  })
  @ExposeName()
  @IsString({ message: "本地文件路径必须是字符串" })
  @IsNotEmpty({ message: "本地文件路径不能为空" })
  @MinLength(5, { message: "本地文件路径长度不能少于5个字符" })
  localFile!: string;

  @ApiProperty({
    description: "上传到 OSS 的目标路径（如 articles/test.docx）",
    example: "articles/test.docx",
  })
  @ExposeName()
  @IsString({ message: "OSS目标路径必须是字符串" })
  @IsNotEmpty({ message: "OSS目标路径不能为空" })
  @MinLength(5, { message: "OSS目标路径长度不能少于5个字符" })
  ossFile!: string;
}
