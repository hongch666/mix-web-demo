declare module '@fastify/multipart' {
  import { FastifyPluginCallback } from 'fastify';

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
