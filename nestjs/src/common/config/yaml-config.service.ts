import * as yaml from 'js-yaml';
import * as fs from 'fs';
import { config } from 'dotenv';

// 加载 .env 文件
config();

/**
 * 递归解析YAML中的环境变量占位符
 * 支持格式：${VAR_NAME:default_value} 或 ${VAR_NAME}
 */
function resolveEnvVars(obj: unknown): unknown {
  if (typeof obj === 'string') {
    // 匹配 ${VAR_NAME:default_value} 或 ${VAR_NAME}
    return obj.replace(
      /\$\{([^:}]+)(?::([^}]*))?\}/g,
      (_: string, key: string, defaultVal?: string): string => {
        const value: string | undefined = process.env[key];
        if (value !== undefined) {
          return value;
        }
        return defaultVal !== undefined ? defaultVal : '';
      },
    );
  }
  if (Array.isArray(obj)) {
    return obj.map((item: unknown): unknown => resolveEnvVars(item));
  }
  if (obj !== null && typeof obj === 'object') {
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

export default (): Record<string, unknown> => {
  const YAML_CONFIG_FILENAME: string = 'application.yaml'; // 项目根目录路径
  const fileContents: string = fs.readFileSync(YAML_CONFIG_FILENAME, 'utf8');
  let configObj: Record<string, unknown> = yaml.load(fileContents) as Record<
    string,
    unknown
  >;

  // 递归替换环境变量
  configObj = resolveEnvVars(configObj) as Record<string, unknown>;

  return configObj;
};
