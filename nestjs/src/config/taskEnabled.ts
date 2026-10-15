/**
 * 定时任务开关解析
 * 配置段缺失或未声明 task.enabled 时默认启用，与本地调度器既有行为保持一致
 */
export function isTaskEnabled(config: Record<string, unknown>): boolean {
  const task: unknown = config.task;
  if (task === null || typeof task !== "object") {
    return true;
  }
  const enabled: unknown = (task as Record<string, unknown>).enabled;
  if (typeof enabled === "boolean") {
    return enabled;
  }
  if (typeof enabled === "string") {
    return ["true", "1", "yes", "on"].includes(enabled.trim().toLowerCase());
  }
  return true;
}
