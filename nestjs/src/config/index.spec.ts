import { resolveEnvVars } from "./index";

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
