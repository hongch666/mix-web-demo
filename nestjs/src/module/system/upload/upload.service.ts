import { Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as crypto from "crypto";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { logger } from "src/common/utils/writeLog";
import { OssService } from "src/module/common/oss/oss.service";
import { pipeline, Readable } from "stream";
import { promisify } from "util";
import { UploadResult } from "./dto/upload.dto";

const pump = promisify(pipeline);

export interface MultipartUploadFile {
  filename?: string;
  readable?: boolean;
  pipe?: unknown;
  file?: Readable;
  toBuffer?: () => Promise<Buffer>;
}

@Injectable()
export class UploadService {
  constructor(
    private readonly ossService: OssService,
    private readonly configService: ConfigService,
  ) {}

  /**
   * 上传本地文件到 OSS
   */
  async uploadFile(localFile: string, ossFile: string): Promise<string> {
    return this.ossService.uploadFile(localFile, ossFile);
  }

  /**
   * 上传图片到 OSS
   */
  async uploadImage(file: MultipartUploadFile): Promise<UploadResult> {
    logger.info(Messages.UPLOAD_IMAGE_START(file?.filename));
    logger.info(
      Messages.UPLOAD_FILE_TYPE_INFO(
        typeof file,
        file?.readable,
        typeof file?.pipe,
      ),
    );
    logger.info(Messages.UPLOAD_FILE_KEYS(Object.keys(file || {}).join(", ")));

    const originalFilename: string = file.filename || "image";
    const fileExtension: string =
      path.extname(originalFilename).toLowerCase() || ".jpg";
    const uniqueFilename: string = `${crypto.randomUUID()}${fileExtension}`;
    logger.info(Messages.UPLOAD_GENERATED_FILENAME(uniqueFilename));

    // 保存到本地临时目录
    logger.info(Messages.FILE_SAVE_TEMP_START);
    const localPath: string = await this.saveFileToTemp(file, uniqueFilename, [
      ".png",
      ".jpg",
      ".jpeg",
      ".gif",
      ".webp",
    ]);
    logger.info(Messages.UPLOAD_FILE_SAVED_TO_TEMP(localPath));

    try {
      // 上传到 OSS
      logger.info(Messages.FILE_UPLOAD_OSS_START);
      const ossPath: string = `pic/${uniqueFilename}`;
      logger.info(Messages.UPLOAD_OSS_TARGET_PATH(ossPath));

      const ossUrl: string = await this.ossService.uploadFile(
        localPath,
        ossPath,
      );
      logger.info(Messages.UPLOAD_OSS_COMPLETED(ossUrl));

      return {
        originalFilename,
        ossFilename: uniqueFilename,
        ossUrl,
      };
    } finally {
      // 删除本地临时文件
      logger.info(Messages.FILE_CLEANUP_START);
      await this.cleanupTempFile(localPath);
      logger.info(Messages.FILE_CLEANUP_COMPLETED);
    }
  }

  /**
   * 上传 PDF 到 OSS
   */
  async uploadPdf(
    file: MultipartUploadFile,
    customFilename?: string,
  ): Promise<UploadResult> {
    logger.info(Messages.UPLOAD_PDF_START(file?.filename));

    const originalFilename: string = file.filename || "document.pdf";
    const fileExtension: string = path.extname(originalFilename).toLowerCase();

    if (fileExtension !== ".pdf") {
      throw BusinessException.unprocessableEntity(Messages.ONLY_PDF_SUPPORTED);
    }

    // 如果提供了自定义文件名，使用自定义文件名；否则生成 UUID
    let uniqueFilename: string;
    if (customFilename) {
      uniqueFilename = `${customFilename}.pdf`;
    } else {
      uniqueFilename = `${crypto.randomUUID()}${fileExtension}`;
    }
    logger.info(Messages.UPLOAD_GENERATED_FILENAME(uniqueFilename));

    // 保存到本地临时目录
    logger.info(Messages.FILE_SAVE_TEMP_START);
    const localPath: string = await this.saveFileToTemp(file, uniqueFilename);
    logger.info(Messages.UPLOAD_FILE_SAVED_TO_TEMP(localPath));

    try {
      // 上传到 OSS
      logger.info(Messages.FILE_UPLOAD_OSS_START);
      const ossPath: string = `pdf/${uniqueFilename}`;
      logger.info(Messages.UPLOAD_OSS_TARGET_PATH(ossPath));

      const ossUrl: string = await this.ossService.uploadFile(
        localPath,
        ossPath,
      );
      logger.info(Messages.UPLOAD_OSS_COMPLETED(ossUrl));

      return {
        originalFilename,
        ossFilename: uniqueFilename,
        ossUrl,
      };
    } finally {
      // 删除本地临时文件
      logger.info(Messages.FILE_CLEANUP_START);
      await this.cleanupTempFile(localPath);
      logger.info(Messages.FILE_CLEANUP_COMPLETED);
    }
  }

  private async saveFileToTemp(
    file: MultipartUploadFile,
    filename: string,
    allowExt?: string[],
  ): Promise<string> {
    // 禁用 attachFieldsToBody 后，file 本身就是流对象，有 filename、encoding、mimetype 等属性
    if (!file) {
      throw BusinessException.badRequest(Messages.NO_FILE_UPLOADED);
    }

    const originalFilename: string = file.filename || "";
    if (allowExt && allowExt.length > 0) {
      const ext: string = path.extname(originalFilename).toLowerCase() || "";
      if (!allowExt.includes(ext)) {
        logger.error(
          Messages.UPLOAD_UNSUPPORTED_FORMAT(ext, allowExt.join(", ")),
        );
        throw BusinessException.badRequest(
          Messages.UPLOAD_ALLOWED_FORMATS(allowExt.join(", ")),
        );
      }
    }

    // 从配置中获取上传目录，如果没有配置则使用系统临时目录
    let uploadDir: string =
      this.configService.get<string>("files.upload") ||
      path.join(os.tmpdir(), "nestjs-upload");

    // 如果是相对路径，转换为绝对路径
    if (!path.isAbsolute(uploadDir)) {
      uploadDir = path.join(process.cwd(), uploadDir);
    }

    await fs.promises.mkdir(uploadDir, { recursive: true });
    const localPath = path.join(uploadDir, filename);

    try {
      // @fastify/multipart 返回的对象有 file 属性是真正的 Readable stream
      logger.info(Messages.UPLOAD_CHECK_FILE_PROPERTY(typeof file?.file));

      if (!file.file) {
        // 如果没有 file.file 属性，尝试使用 toBuffer() 方法
        if (typeof file.toBuffer === "function") {
          logger.info(Messages.USING_TO_BUFFER_METHOD);
          const buffer: Buffer = await file.toBuffer();
          await fs.promises.writeFile(localPath, buffer);
          logger.info(Messages.UPLOAD_FILE_SAVED_TO_TEMP(localPath));
          return localPath;
        } else {
          throw BusinessException.unprocessableEntity(
            Messages.FILE_NO_VALID_METHOD,
          );
        }
      }

      // 使用 file.file 作为流
      logger.info(
        Messages.UPLOAD_USE_FILE_STREAM(
          typeof file.file,
          typeof file.file?.pipe,
        ),
      );
      await pump(file.file, fs.createWriteStream(localPath));
      logger.info(Messages.UPLOAD_FILE_SAVED_TO_TEMP(localPath));
      return localPath;
    } catch (error: unknown) {
      if (error instanceof BusinessException) {
        throw error;
      }
      const message = error instanceof Error ? error.message : String(error);
      logger.error(Messages.UPLOAD_SAVE_TO_TEMP_FAILED(message));
      throw error;
    }
  }

  private async cleanupTempFile(filePath: string): Promise<void> {
    try {
      await fs.promises.unlink(filePath);
      logger.info(Messages.UPLOAD_TEMP_FILE_DELETED(filePath));
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      logger.warning(Messages.UPLOAD_DELETE_TEMP_FAILED(message));
    }
  }
}
