import { HttpCode } from "../constants";
import { error, success } from "./response";

describe("response helpers", () => {
  it("creates a success response with data and default message", () => {
    expect(success({ id: 1 })).toEqual({
      code: HttpCode.OK,
      msg: "success",
      data: { id: 1 },
    });
  });

  it("preserves a custom success message and supports null-like data", () => {
    expect(success(null, "created")).toEqual({
      code: HttpCode.OK,
      msg: "created",
      data: null,
    });
  });

  it("creates an error response with null data and default message", () => {
    expect(error(404)).toEqual({ code: 404, msg: "failed", data: null });
    expect(error(422, "invalid input")).toEqual({
      code: 422,
      msg: "invalid input",
      data: null,
    });
  });
});
