import { ConfigModule, ConfigService } from "@nestjs/config";
import { Module, Provider } from "@nestjs/common";
import type OSS from "ali-oss";
import { OssClient, OssService } from "./oss.service";
import { OSS_CLIENT } from "./oss.tokens";

const ossClientProvider: Provider = {
  provide: OSS_CLIENT,
  inject: [ConfigService],
  useFactory: async (
    configService: ConfigService,
  ): Promise<OssClient | null> => {
    const config: Record<string, unknown> =
      configService.get<Record<string, unknown>>("oss") ?? {};
    const accessKeyId: string | undefined =
      (config["access_key_id"] as string) || (config["accessKeyId"] as string);
    const accessKeySecret: string | undefined =
      (config["access_key_secret"] as string) ||
      (config["accessKeySecret"] as string);
    const bucketName: string =
      (config["bucket_name"] as string) || (config["bucketName"] as string);
    const endpoint: string = (config["endpoint"] as string) || "";
    if (!accessKeyId || !accessKeySecret || !bucketName || !endpoint) {
      return null;
    }
    const { default: AliOss } = await import("ali-oss");
    const client: OSS = new AliOss({
      accessKeyId,
      accessKeySecret,
      bucket: bucketName,
      endpoint,
      secure: true,
      enableProxy: true,
    });
    return client;
  },
};

@Module({
  imports: [ConfigModule],
  providers: [ossClientProvider, OssService],
  exports: [OssService],
})
export class OssModule {}
