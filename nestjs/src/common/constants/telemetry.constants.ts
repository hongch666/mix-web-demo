/** OpenTelemetry 配置与日志关联常量 */
export class TelemetryConstants {
  // ===== 采样器 =====

  /** 全量采样 */
  static readonly SAMPLER_ALWAYS_ON = "always_on";
  /** 不采样 */
  static readonly SAMPLER_ALWAYS_OFF = "always_off";
  /** 按 trace id 比例采样 */
  static readonly SAMPLER_TRACE_ID_RATIO = "traceidratio";
  /** 跟随父级上下文，父级存在时按父级决策，否则全量采样 */
  static readonly SAMPLER_PARENT_ALWAYS_ON = "parentbased_always_on";
  /** 跟随父级上下文，父级存在时按父级决策，否则不采样 */
  static readonly SAMPLER_PARENT_ALWAYS_OFF = "parentbased_always_off";
  /** 跟随父级上下文，父级缺失时按 trace id 比例采样 */
  static readonly SAMPLER_PARENT_TRACE_ID_RATIO = "parentbased_traceidratio";

  // ===== 链路标识 =====

  /** 无链路时使用的占位 trace id */
  static readonly EMPTY_TRACE_ID = "-";
  /** 日志中链路标识的字段名 */
  static readonly TRACE_ID_FIELD = "trace_id";
}
