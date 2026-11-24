在本仓库生成或修改代码时，基于 mix-web-demo 系列 skills 进行分析实现：

1. 先加载 `mix-web-demo` 总入口，遵守其中的通用规则与任务路由
2. 再按任务加载对应专项技能：
   - `spring/` → `mix-spring`
   - `gozero/`（含 `.api`/goctl） → `mix-gozero`
   - `nestjs/` → `mix-nestjs`
   - `fastapi/` → `mix-fastapi`
   - `gateway/` → `mix-gateway`
   - 建表/查询/索引/`db/**` → `mix-db`
   - Dockerfile / `.dockerignore` / 镜像 → `mix-docker`
   - 仓库工程 / 工具链 / `mix` 命令 / 令牌 → `mix-engineering`
   - 接口变更收尾 / 测试 / 验证 / 交付 → `mix-workflow`（测试还需读其 `references/unit-testing.md`）
3. 专项技能与通用 skills 冲突时，以本仓库 `mix-*` 技能为准
