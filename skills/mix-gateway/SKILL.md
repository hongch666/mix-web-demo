---
name: mix-gateway
description: mix-web-demo 的 Apache APISIX 网关配置专项规范，覆盖路由分组、forward-auth 认证、限流、内部接口黑名单与端口收敛。修改 gateway/ 下配置时加载
---

# mix-gateway 网关规范

## 网关（gateway/，Apache APISIX）

- 以 YAML 数据面运行（`role_data_plane` + `config_provider: yaml`），无业务代码；路由与插件全部在 `apisix/apisix.yaml`
- 静态文档：`gateway/swagger-ui` → `/swagger-ui/`（Swagger UI，可在线调试），由 `nginx_config.http_server_configuration_snippet` 的 `location` + compose 挂载提供；新增静态目录按同一模式加 volume 与 `location`
- Swagger UI 页面自带「导出 Markdown」按钮：`gateway/swagger-ui/markdown-export.js` 在浏览器里把页面上已加载的各服务规范（Tab 上的 `data-url`，即 `/swagger/*.json`）实时转成 Markdown 并下载，**不依赖仓库里任何预生成文件**；改导出格式只改这个脚本，四个服务新增接口无需重新生成产物
- **认证外置**：业务路由挂 `forward-auth` 回调 Spring 的 `/users/internal/auth/validate`，由网关注入 `X-User-Id` / `X-Username` / `X-Session-Id` 供下游透传；**下游服务只信任请求头**，不自行解析 JWT
- 内部接口防护靠 `block-internal` 路由（URI 黑名单），新增内部接口必须同步加入黑名单
- **`block-internal` 的 `uri` 是精确匹配**（只有以 `*` 结尾才是前缀匹配），而它要挡的接口往往落在宽松前缀路由（`/articles/*`、`/users/*`、`/email/*`、`/ai_history/*`）覆盖范围内。新增内部接口时除了加黑名单，还要确认黑名单条目能覆盖实际访问路径，否则会出现「精确路径被挡、子路径可直达」的缺口
- 长连接用独立 upstream（读超时 3600s），与普通接口区分
- **限流策略是 `local`，网关不接 Redis**：`nginx_config.worker_processes` 已固定为 1，`limit-req` 的进程内计数就是全局配额，所以 `*login_limit` 锚点里只有 `policy: local`，不要再加回 `redis_host` / `redis_password` / `redis_database`。扩多 worker 或多副本时配额会按实例数放大，届时改回 `policy: redis` 并补齐 `redis_*`（含密码，`redis` 容器强制 `requirepass`），同时注意 `allow_degradation` 默认 false 会让 Redis 故障直接打挂登录接口
- 新增对外路由：按既有分组挂 `forward-auth` 与 `limit-req`（登录类用 `*login_limit`）；public 路由必须有明确理由且不能漏挂限流
- 改配置后用 YAML 解析器校验语法，并确认目标路由的插件确实挂载
- **端口暴露**：根 `docker-compose.yml` 里只有 gateway 映射宿主机（8080 → 容器 9080），spring / gozero / nestjs / fastapi **均不映射宿主机端口**，容器间经 `hcsy` 网络 + Nacos 直连。下游无条件信任 `X-User-Id`，所以这个收敛状态正是身份不可伪造的前提，改动编排时不要给业务服务加回 `ports`；本地开发模式（`./mix dev seq`）直连服务端口，没有这层保护
