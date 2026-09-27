import { Logger } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import type { NestFastifyApplication } from "@nestjs/platform-fastify";
import { FastifyAdapter } from "@nestjs/platform-fastify";
import type { OpenAPIObject } from "@nestjs/swagger";
import type { DumpOptions } from "js-yaml";
import { dump as yamlDump } from "js-yaml";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { AppModule } from "src/app/app.module";
import { buildSwaggerDocument } from "src/app/swagger";

const LOG_CONTEXT = "OpenApiGenerator";
const DEFAULT_OUTPUT_FILE = "docs/openapi.json";

/** YAML 产物：noRefs 避免生成锚点与别名，skipInvalid 容忍 undefined 字段 */
const YAML_DUMP_OPTIONS: DumpOptions = { noRefs: true, skipInvalid: true };

/**
 * 离线生成 NestJS 侧的 OpenAPI 静态产物（JSON 与 YAML 两份）
 *
 * 使用 preview 模式创建应用：provider 与 controller 不会被实例化，
 * 因此不会连接 MongoDB / MySQL / Redis / RabbitMQ，也不需要启动 HTTP 服务
 * 产物默认写入 NestJS 模块自身的 docs/openapi.json 与 docs/openapi.yaml，
 * 可用 OPENAPI_OUTPUT_FILE 覆盖 JSON 路径（YAML 取其同名 .yaml）
 */
async function generateOpenApiDoc(): Promise<void> {
  const app: NestFastifyApplication =
    await NestFactory.create<NestFastifyApplication>(
      AppModule,
      new FastifyAdapter(),
      { preview: true },
    );

  try {
    const document: OpenAPIObject = buildSwaggerDocument(app);
    const outputFile: string = resolve(
      process.env.OPENAPI_OUTPUT_FILE ?? DEFAULT_OUTPUT_FILE,
    );
    const yamlOutputFile: string = outputFile.replace(/\.json$/i, ".yaml");

    await mkdir(dirname(outputFile), { recursive: true });
    await writeFile(
      outputFile,
      `${JSON.stringify(document, null, 2)}\n`,
      "utf8",
    );
    await writeFile(
      yamlOutputFile,
      yamlDump(document, YAML_DUMP_OPTIONS),
      "utf8",
    );

    const pathCount: number = Object.keys(document.paths ?? {}).length;
    Logger.log(
      `NestJS OpenAPI 文档已生成: ${outputFile}、${yamlOutputFile}（接口路径 ${pathCount} 个）`,
      LOG_CONTEXT,
    );
  } finally {
    await app.close();
  }
}

void generateOpenApiDoc().catch((error: unknown) => {
  Logger.error("NestJS OpenAPI 文档生成失败", error, LOG_CONTEXT);
  process.exit(1);
});
