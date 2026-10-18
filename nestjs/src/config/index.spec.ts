import { isTaskEnabled, resolveEnvVars } from "./index";

describe("config resolveEnvVars", () => {
  const valueKey = "CONFIG_TEST_VALUE";
  const boolKey = "CONFIG_TEST_BOOL";

  afterEach((): void => {
    delete process.env[valueKey];
    delete process.env[boolKey];
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", (): void => {
    process.env[valueKey] = "from-env";

    expect(resolveEnvVars("${CONFIG_TEST_VALUE}")).toBe("from-env");
    expect(resolveEnvVars("${CONFIG_TEST_MISSING:fallback}")).toBe("fallback");
    expect(resolveEnvVars("${CONFIG_TEST_MISSING}")).toBe("");
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", (): void => {
    process.env[boolKey] = "true";

    expect(resolveEnvVars("${CONFIG_TEST_BOOL}")).toBe(true);
    expect(resolveEnvVars("${CONFIG_TEST_NULL:null}")).toBeNull();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", (): void => {
    process.env[valueKey] = "42";

    expect(
      resolveEnvVars({
        list: ["${CONFIG_TEST_VALUE}"],
        nested: { key: "${CONFIG_TEST_VALUE}" },
      }),
    ).toEqual({ list: ["42"], nested: { key: "42" } });
  });
});

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
