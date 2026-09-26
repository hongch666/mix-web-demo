import { HttpCode } from "../constants";
import { error, success } from "./response";

describe("response helpers", () => {
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", () => {
    expect(success({ id: 1 })).toEqual({
      code: HttpCode.OK,
      msg: "success",
      data: { id: 1 },
    });
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", () => {
    expect(success(null, "created")).toEqual({
      code: HttpCode.OK,
      msg: "created",
      data: null,
    });
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", () => {
    expect(error(404)).toEqual({ code: 404, msg: "failed", data: null });
    expect(error(422, "invalid input")).toEqual({
      code: 422,
      msg: "invalid input",
      data: null,
    });
  });
});
