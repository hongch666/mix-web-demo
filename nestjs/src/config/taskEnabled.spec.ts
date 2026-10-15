import { isTaskEnabled } from "./taskEnabled";

describe("isTaskEnabled", () => {
  it("配置段缺失或未声明 enabled 时默认启用", () => {
    expect(isTaskEnabled({})).toBe(true);
    expect(isTaskEnabled({ task: null })).toBe(true);
    expect(isTaskEnabled({ task: {} })).toBe(true);
    expect(isTaskEnabled({ task: { enabled: true } })).toBe(true);
  });

  it("enabled 为 false 时关闭本地定时任务", () => {
    expect(isTaskEnabled({ task: { enabled: false } })).toBe(false);
  });

  it("字符串形式的开关值按大小写与空白不敏感解析", () => {
    expect(isTaskEnabled({ task: { enabled: "false" } })).toBe(false);
    expect(isTaskEnabled({ task: { enabled: " FALSE " } })).toBe(false);
    expect(isTaskEnabled({ task: { enabled: "true" } })).toBe(true);
    expect(isTaskEnabled({ task: { enabled: "1" } })).toBe(true);
  });

  it("无法识别的开关值回退为启用", () => {
    expect(isTaskEnabled({ task: { enabled: null } })).toBe(true);
    expect(isTaskEnabled({ task: { enabled: 0 } })).toBe(true);
    expect(isTaskEnabled({ task: "enabled" })).toBe(true);
  });
});
