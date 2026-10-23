/* eslint-disable @typescript-eslint/no-explicit-any */

import { SpringClientService } from "./springClient.service";

// 用假的 NacosService 构造被测服务：本类只负责构造请求，远程调用、重试与内部令牌注入由 NacosService.call 承担（那边已有覆盖）
function createService(call: jest.Mock = jest.fn().mockResolvedValue({})) {
  const service = new SpringClientService({ call } as any);
  return { service, call };
}

describe("SpringClientService", () => {
  it("验证 getUserById 把调用委托给 Nacos 并原样返回其响应", async () => {
    const call = jest.fn().mockResolvedValue({ id: 7 });
    const { service } = createService(call);
    await expect(service.getUserById(7)).resolves.toEqual({ id: 7 });
    expect(call).toHaveBeenCalled();
  });

  describe("请求构造", () => {
    // serviceName / method / path / body / queryParams 是与 Spring 内部接口的契约，逐个固定
    const cases: {
      name: string;
      invoke: (service: SpringClientService) => Promise<unknown>;
      expected: Record<string, unknown>;
    }[] = [
      {
        name: "getUserById 按 /users/{id} 发起 GET",
        invoke: (service) => service.getUserById(7),
        expected: { serviceName: "spring", method: "GET", path: "/users/7" },
      },
      {
        name: "getUserByIds 按 /users/batch 发起 POST 并透传 ids",
        invoke: (service) => service.getUserByIds([1, 2]),
        expected: {
          serviceName: "spring",
          method: "POST",
          path: "/users/batch",
          body: { ids: [1, 2] },
        },
      },
      {
        name: "getUsersByName 按 /users/by-name 发起 GET 并透传 name",
        invoke: (service) => service.getUsersByName("alice"),
        expected: {
          serviceName: "spring",
          method: "GET",
          path: "/users/by-name",
          queryParams: { name: "alice" },
        },
      },
      {
        name: "findOrCreateGithubUser 按 /users/github-user 发起 POST 并透传 dto",
        invoke: (service) => service.findOrCreateGithubUser({ login: "alice" }),
        expected: {
          serviceName: "spring",
          method: "POST",
          path: "/users/github-user",
          body: { login: "alice" },
        },
      },
      {
        name: "isAdminUser 按 /users/{id}/is-admin 发起 GET",
        invoke: (service) => service.isAdminUser(7),
        expected: {
          serviceName: "spring",
          method: "GET",
          path: "/users/7/is-admin",
        },
      },
      {
        name: "createTokenTicket 按 /users/github/token-ticket 发起 POST",
        invoke: (service) => service.createTokenTicket(7, "alice"),
        expected: {
          serviceName: "spring",
          method: "POST",
          path: "/users/github/token-ticket",
          body: { user_id: 7, username: "alice" },
          headers: { "X-Username": "alice" },
        },
      },
      {
        name: "getArticleById 按 /articles/{id} 发起 GET",
        invoke: (service) => service.getArticleById(3),
        expected: { serviceName: "spring", method: "GET", path: "/articles/3" },
      },
      {
        name: "getArticleByIds 按 /articles/batch 发起 POST 并透传 ids",
        invoke: (service) => service.getArticleByIds([3, 4]),
        expected: {
          serviceName: "spring",
          method: "POST",
          path: "/articles/batch",
          body: { ids: [3, 4] },
        },
      },
      {
        name: "getArticlesByTitle 按 /articles/by-title 发起 GET 并透传 title",
        invoke: (service) => service.getArticlesByTitle("Go"),
        expected: {
          serviceName: "spring",
          method: "GET",
          path: "/articles/by-title",
          queryParams: { title: "Go" },
        },
      },
    ];

    for (const testCase of cases) {
      it(`验证 ${testCase.name}`, async () => {
        const { service, call } = createService();

        await testCase.invoke(service);

        expect(call).toHaveBeenCalledTimes(1);
        expect(call).toHaveBeenCalledWith(testCase.expected);
      });
    }
  });

  describe("createTokenTicket 的用户名清洗", () => {
    // X-Username 只允许可打印 ASCII：非 ASCII 必须剥离，body 里保留原文
    const cases: { name: string; username: string; wantHeader: string }[] = [
      { name: "可打印 ASCII 原样保留", username: "alice", wantHeader: "alice" },
      { name: "首尾空白被去除", username: "  alice  ", wantHeader: "alice" },
      {
        name: "中文等非 ASCII 字符被剥离",
        username: "张三 zhangsan",
        wantHeader: "zhangsan",
      },
      { name: "全为非 ASCII 时请求头为空", username: "张三", wantHeader: "" },
    ];

    for (const testCase of cases) {
      it(`验证 ${testCase.name}`, async () => {
        const { service, call } = createService();

        await service.createTokenTicket(7, testCase.username);

        expect(call).toHaveBeenCalledWith({
          serviceName: "spring",
          method: "POST",
          path: "/users/github/token-ticket",
          body: { user_id: 7, username: testCase.username },
          headers: { "X-Username": testCase.wantHeader },
        });
      });
    }
  });

  describe("返回值与异常透传", () => {
    it("验证 extractData 取统一响应里的 data 字段", () => {
      expect(
        SpringClientService.extractData<{ id: number }>({
          code: 200,
          data: { id: 7 },
        }),
      ).toEqual({ id: 7 });
    });

    it("验证 Nacos 调用失败时原样抛出错误", async () => {
      const { service } = createService(
        jest.fn().mockRejectedValue(new Error("spring unavailable")),
      );

      await expect(service.getUserById(7)).rejects.toThrow(
        "spring unavailable",
      );
    });
  });
});
