/** OpenTelemetry 配置与日志关联常量 */
export class TelemetryConstants {
  static readonly SAMPLER_ALWAYS_ON = "always_on";
  static readonly SAMPLER_ALWAYS_OFF = "always_off";
  static readonly SAMPLER_TRACE_ID_RATIO = "traceidratio";
  static readonly SAMPLER_PARENT_ALWAYS_ON = "parentbased_always_on";
  static readonly SAMPLER_PARENT_ALWAYS_OFF = "parentbased_always_off";
  static readonly SAMPLER_PARENT_TRACE_ID_RATIO =
    "parentbased_traceidratio";

  static readonly EMPTY_TRACE_ID = "-";
  static readonly TRACE_ID_FIELD = "trace_id";
}
