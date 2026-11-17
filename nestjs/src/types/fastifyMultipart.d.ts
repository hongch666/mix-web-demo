declare module "@fastify/multipart" {
  import { FastifyPluginCallback } from "fastify";

  export interface MultipartFile {
    file: NodeJS.ReadableStream;
    filename: string;
    encoding: string;
    mimetype: string;
  }

  export interface MultipartField {
    fieldname: string;
    value: string;
  }

  export interface MultipartOptions {
    attachFieldsToBody?: boolean;
    /** 超过 limits.fileSize 时是否直接抛错，关闭后由业务层按 truncated 标记处理 */
    throwFileSizeLimit?: boolean;
    limits?: {
      fileSize?: number;
      files?: number;
      fields?: number;
      fieldNameSize?: number;
      fieldSize?: number;
    };
  }

  const plugin: FastifyPluginCallback<MultipartOptions>;
  export default plugin;
}
