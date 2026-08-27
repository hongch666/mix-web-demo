import { Injectable, Logger as NestLogger, OnModuleInit } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as fs from "fs";
import * as path from "path";
import { Messages } from "src/common/constants";

/**
 * 日志服务
 *
 * 统一负责控制台输出与文件落盘，通过依赖注入获取配置，
 * 替代原先模块级单例的工具类实现
 */
@Injectable()
export class LoggerService implements OnModuleInit {
  private readonly nestLogger = new NestLogger(LoggerService.name);
  private logPath!: string;

  constructor(private readonly configService: ConfigService) {}

  /**
   * 模块初始化时加载日志配置
   */
  onModuleInit(): void {
    this.loadConfig();
  }

  /**
   * 加载日志目录配置
   * 支持 LOG_PATH 环境变量覆盖，其次读取 YAML 配置的 logs.path
   */
  private loadConfig(): void {
    try {
      const logPathFromEnv: string | undefined =
        this.configService.get<string>("LOG_PATH");
      const logPathFromYaml: string | undefined =
        this.configService.get<string>("logs.path");

      this.logPath = logPathFromEnv || logPathFromYaml || "logs";
      this.nestLogger.log(Messages.LOG_CONFIG_LOADED(this.logPath));
    } catch (error: unknown) {
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      throw new Error(Messages.LOG_CONFIG_LOAD_FAILED(errorMessage));
    }
  }

  /**
   * 直接写入日志到文件
   * @param message 日志消息
   * @param level 日志级别
   */
  private writeFileLog(message: string, level: string): void {
    // 确保日志目录存在
    if (!fs.existsSync(this.logPath)) {
      fs.mkdirSync(this.logPath, { recursive: true });
    }

    // 日志文件名 (按日期)
    const now: Date = new Date();
    const year: number = now.getFullYear();
    const month: string = String(now.getMonth() + 1).padStart(2, "0");
    const day: string = String(now.getDate()).padStart(2, "0");
    const today: string = `${year}-${month}-${day}`;
    const logFile: string = path.join(this.logPath, `app_${today}.log`);

    // 格式化日志消息（使用本地时间）
    const hours: string = String(now.getHours()).padStart(2, "0");
    const minutes: string = String(now.getMinutes()).padStart(2, "0");
    const seconds: string = String(now.getSeconds()).padStart(2, "0");
    const timestamp: string = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    const logEntry: string = `${timestamp} - ${level} - ${message}\n`;

    try {
      fs.appendFileSync(logFile, logEntry, "utf8");
    } catch (error: unknown) {
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      throw new Error(Messages.LOG_WRITE_FAILED(errorMessage));
    }
  }

  /**
   * 记录信息级别日志
   * @param message 日志消息
   */
  info(message: string): void {
    this.nestLogger.log(message);
    this.writeFileLog(message, "INFO");
  }

  /**
   * 记录错误级别日志
   * @param message 日志消息
   */
  error(message: string): void {
    this.nestLogger.error(message);
    this.writeFileLog(message, "ERROR");
  }

  /**
   * 记录警告级别日志
   * @param message 日志消息
   */
  warning(message: string): void {
    this.nestLogger.warn(message);
    this.writeFileLog(message, "WARNING");
  }

  /**
   * 记录调试级别日志
   * @param message 日志消息
   */
  debug(message: string): void {
    this.nestLogger.debug(message);
    this.writeFileLog(message, "DEBUG");
  }
}
