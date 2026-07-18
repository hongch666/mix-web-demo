import { config as loadDotenv } from "dotenv";
import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

/**
 * 配置文件加载入口
 * - 从当前模块同级目录读取 application.yaml
 * - 从项目根目录加载 .env（保留原始位置不变）
 * - 解析 YAML 中 ${VAR:default} 占位符为环境变量实际值
 */

// 项目根目录：定位到包含 src/config 的目录
// 开发态 __dirname = nestjs/src/config；编译后 __dirname = nestjs/dist/config
const PROJECT_ROOT: string = path.resolve(__dirname, "..", "..");

// 加载根目录下的 .env（不影响原本位于 nestjs/.env 的文件位置）
const dotenvPath: string = path.join(PROJECT_ROOT, ".env");
if (fs.existsSync(dotenvPath)) {
  loadDotenv({ path: dotenvPath });
}

/**
 * 递归解析 YAML 中的环境变量占位符
 * 支持格式：${VAR_NAME:default_value} 或 ${VAR_NAME}
 */
function resolveEnvVars(obj: unknown): unknown {
  if (typeof obj === "string") {
    return obj.replace(
      /\$\{([^:}]+)(?::([^}]*))?\}/g,
      (_: string, key: string, defaultVal?: string): string => {
        const value: string | undefined = process.env[key];
        if (value !== undefined) {
          return value;
        }
        return defaultVal !== undefined ? defaultVal : "";
      },
    );
  }
  if (Array.isArray(obj)) {
    return obj.map((item: unknown): unknown => resolveEnvVars(item));
  }
  if (obj !== null && typeof obj === "object") {
    return Object.entries(obj as Record<string, unknown>).reduce(
      (
        acc: Record<string, unknown>,
        [key, val]: [string, unknown],
      ): Record<string, unknown> => {
        acc[key] = resolveEnvVars(val);
        return acc;
      },
      {} as Record<string, unknown>,
    );
  }
  return obj;
}

// 读取并解析 application.yaml
const yamlPath: string = path.join(__dirname, "application.yaml");
const fileContents: string = fs.readFileSync(yamlPath, "utf8");
let parsed: Record<string, unknown> = yaml.load(fileContents) as Record<
  string,
  unknown
>;

// 递归替换环境变量
parsed = resolveEnvVars(parsed) as Record<string, unknown>;

const config: Record<string, unknown> = parsed;

export default config;
