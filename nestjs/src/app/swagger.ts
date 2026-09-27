import type { INestApplication } from "@nestjs/common";
import type { OpenAPIObject } from "@nestjs/swagger";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import { SwaggerConfig } from "src/common/constants";
import { applySwaggerSnakeCase } from "src/common/utils/swaggerSnakeCase";

/**
 * 构建 Swagger/OpenAPI 文档对象
 *
 * 运行时（app/index.ts）与离线生成脚本（script/generateOpenapi.ts）共用同一份构建逻辑，
 * 避免两处配置漂移
 */
export function buildSwaggerDocument(app: INestApplication): OpenAPIObject {
  const swaggerBuilder = new DocumentBuilder()
    .setTitle(SwaggerConfig.SWAGGER_TITLE)
    .setDescription(SwaggerConfig.SWAGGER_DESCRIPTION)
    .setVersion(SwaggerConfig.SWAGGER_VERSION);

  SwaggerConfig.SWAGGER_TAGS.forEach(([name, description]) => {
    swaggerBuilder.addTag(name, description);
  });

  const config: Omit<OpenAPIObject, "paths"> = swaggerBuilder.build();
  return applySwaggerSnakeCase(SwaggerModule.createDocument(app, config));
}
