import { resolveEnvVars } from "./index";

describe("config resolveEnvVars", () => {
  const valueKey = "CONFIG_TEST_VALUE";
  const boolKey = "CONFIG_TEST_BOOL";

  afterEach((): void => {
    delete process.env[valueKey];
    delete process.env[boolKey];
  });

  it("优先使用环境变量并回退到默认值", (): void => {
    process.env[valueKey] = "from-env";

    expect(resolveEnvVars("${CONFIG_TEST_VALUE}")).toBe("from-env");
    expect(resolveEnvVars("${CONFIG_TEST_MISSING:fallback}")).toBe("fallback");
    expect(resolveEnvVars("${CONFIG_TEST_MISSING}")).toBe("");
  });

  it("替换后恢复布尔值与空值类型", (): void => {
    process.env[boolKey] = "true";

    expect(resolveEnvVars("${CONFIG_TEST_BOOL}")).toBe(true);
    expect(resolveEnvVars("${CONFIG_TEST_NULL:null}")).toBeNull();
  });

  it("递归解析嵌套对象与数组中的占位符", (): void => {
    process.env[valueKey] = "42";

    expect(
      resolveEnvVars({
        list: ["${CONFIG_TEST_VALUE}"],
        nested: { key: "${CONFIG_TEST_VALUE}" },
      }),
    ).toEqual({ list: ["42"], nested: { key: "42" } });
  });
});
