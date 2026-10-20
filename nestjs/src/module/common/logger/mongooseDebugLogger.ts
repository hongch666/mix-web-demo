import { inspect } from "util";
import { Messages } from "src/common/constants";
import { LoggerService } from "./logger.service";

// mongoose debug 回调签名：集合名 + 方法名 + 全部参数
export type MongooseDebugLogger = (
  collectionName: string,
  methodName: string,
  ...methodArgs: unknown[]
) => void;

/**
 * 创建 mongoose 调试日志回调
 *
 * 把集合操作日志路由到统一日志服务，写入控制台与按日落盘文件
 * 参数可能包含 Buffer、ObjectId 与循环引用，因此用 inspect 序列化而非 JSON.stringify
 */
export function createMongooseDebugLogger(
  logger: LoggerService,
): MongooseDebugLogger {
  return (
    collectionName: string,
    methodName: string,
    ...methodArgs: unknown[]
  ): void => {
    const args = methodArgs
      .map((arg) =>
        inspect(arg, { depth: 2, breakLength: Infinity, maxArrayLength: 50 }),
      )
      .join(", ");
    logger.debug(Messages.MONGO_DEBUG_LOG(collectionName, methodName, args));
  };
}
