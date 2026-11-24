---
name: mix-engineering
description: mix-web-demo 仓库工程约束专项规范，覆盖行尾、格式化工具、goctl 生成边界、mix 子命令清单、内部令牌与本地依赖环境约束。涉及仓库工程与工具链时加载
---

# mix-engineering 仓库工程规范

## 仓库工程约束

- **禁止删除、清空、移动或重建本地依赖环境**：`fastapi/.venv`、`nestjs/node_modules` 属于开发者本机已安装的依赖环境，删除与整体重建都是禁止操作（重装需联网且耗时，也会打断本地校验命令）；排查问题、清理临时文件、执行格式化与校验时一律绕开这些目录，确需变更依赖时用对应包管理命令做增量安装。**不要为了任何理由运行删除 `.venv` 的命令**（含 `rm -rf`、`Remove-Item -Recurse`、`uv venv --clear`、`python -m venv --clear` 等）
- **Windows 主机上禁止用 WSL 的 bash 跑 `./mix compile fastapi` 与 `./mix test fastapi`（本问题只在 Windows + WSL 场景出现，Linux/macOS 无此问题）**：这两步底层分别是 `uv run python -c ...` 与 `uv run pytest`。在 Windows + WSL 的组合下，WSL bash 里 `uv` / `ruff` / `python3` 解析到的是 Linux 版本，`fastapi/.venv` 却是 Windows 的 uv 创建的（`pyvenv.cfg` 里 `home = C:\...`）；Linux uv 判定环境与自身平台不匹配后，会按 `uv run` 的 sync 语义**清空并重建 `.venv`**，一旦中途被打断就留下半成品，`fastapi/pyproject.toml` 的 `venvPath = "."` / `venv = ".venv"` 随即解析失败并回退到根目录或全局解释器，表现为「IDE 只能解析到根目录的环境」，等价于「重建本地依赖环境」，属禁止操作。Linux/macOS 上 `uv` 与 `.venv` 同平台，`uv run pytest` 就是正常入口，不受本条约束
  - 正确做法（Windows）：`./mix` 只在 Git Bash（且 PATH 指向 Windows 工具）执行；fastapi 的校验改用项目自带解释器做只读操作——`fastapi/.venv/Scripts/python.exe -m pytest -q`、`fastapi/.venv/Scripts/python.exe -m ruff check .`，以及 `scripts/quality/compile.sh` 里那段字节码编译片段。macOS/Linux 上按默认命令执行 `uv run pytest` 即可
  - 全服务形式同样禁止（Windows + WSL 场景）：`./mix compile`、`./mix test` 会把 fastapi 一起带上，要么写明确的服务名、要么改用 Git Bash
  - 唯一例外是技能同步：`./mix skills` 只在技能目录间做镜像复制，不碰依赖环境，在 WSL bash 下可用 `HOME=/mnt/c/Users/<user> ./mix skills` 显式指定目标（见本节的技能同步条目）；除此之外不要自行执行 `uv run` / `uv sync` / `uv venv`
- **Windows 主机上出现下列任一信号就停止用 WSL bash 跑 `./mix`，改用 Git Bash（同样只在 Windows + WSL 下出现）**：`./mix skills` 把技能同步到 `/home/<user>` 而不是 `C:\Users\<user>`（IDE 看到的技能没更新）、`./mix lint gozero` 报 golangci-lint「未安装」而本机其实已安装、`./mix format fastapi` 实际调用的是 Linux ruff。三者都是「bash 解析到了 Linux 工具链」的同一根因，在 WSL bash 下继续跑 `./mix compile` / `./mix test` 就会踩到重建 `.venv` 那条
- 行尾由根目录 `.gitattributes`（`* text=auto eol=lf`）统一为 LF，仓库不再按 CRLF 维护；新建文件不需要手工转换行尾
- 格式化统一走各服务的工具（`./mix format`）：Spring Spotless、GoZero golangci-lint + goctl api format、NestJS Prettier、FastAPI Ruff；不要再手工执行 `gofmt -w` 或 `prettier --write` 做全量重排
- Go 的格式问题用 `./mix lint gozero` 判断（golangci-lint 的 gofmt formatter），不要用裸 `gofmt -l`：它对行尾差异会报大量假阳性
- `goctl`（`api format` / `api go`）生成后由 `genApi.sh` / `genOrm.sh` 自动调用 `./mix format gozero` 收敛格式；手工执行 goctl 时兜底跑一次即可，不需要手工处理行尾
- **goctl 版本不进产物**：`gozero/template/**` 与仓库已生成文件都不包含版本注释（`// goctl {{.version}}`、`//  goctl version: x.y.z`），同一份 `.api` 在不同 goctl 版本下生成结果一致，不会产生无意义的版本 diff；产物是否被人工改动由 `./mix lint gozero` 校验
- **不要在仓库根目录直接执行 goctl**：goctl 在 Windows 下判定模块有缺陷（`go env GOMOD` 返回 `NUL` 而非 `/dev/null`），会以调用者的当前目录为基准回退执行 `go mod init`、`go work use`，在仓库根目录执行会生成多余的 `go.mod` 并把 `go.work` 改成 `use (. / ./gozero/app)`；`./mix goctl-orm`、`./mix goctl-api` 目前仍会触发，执行后确认 `git status` 并清理、还原这两个文件。手工执行 goctl 时先 `cd` 到模块内（如 `gozero/app`）；`checkGenerated.sh` 的生成阶段已切到临时目录执行，不受影响
- git 用于精确核对与回退：`git status --porcelain`、`git diff --ignore-cr-at-eol`（判断是否仅行尾差异）、`git checkout -- <文件>`
- 本机环境参考：Go / gofmt 在 `C:\Program Files\Go\bin\`，goctl 在 `C:\Users\30708\go\bin\goctl.EXE`，git 在 `C:\Program Files\Git\cmd\git.EXE`（`usr\bin\` 下有 grep / tr / sed / basename 等，用完整路径调用），maven 在 `C:\apache-maven-3.9.11\bin\mvn.CMD`，javap 在 `C:\Program Files\Java\jdk-17\bin\javap.exe`
- bash 环境的 `dirname` / `head` 等不稳定（PATH 时有时无），批量格式与行尾校验优先走 `./mix format` / `./mix lint`，需要脚本兜底时用 Python `subprocess` 调绝对路径
- `mix` 脚本顶层子命令有 `setup`、`swag`、`swag-check`、`check-error-codes`、`apifox`、`apifox-check`、`apifox-readme`、`goctl-api`、`goctl-orm`、`lint`、`format`、`test`、`compile`、`token`、`hooks`、`skills`、`dev`、`dist`、`docker`、`docker-services`、`observability`（旧名 `loki` 仍可用，别名 `obs`）、`compose`、`help`；`swag-check` 只读校验静态 OpenAPI 产物与代码是否一致（重新生成后比对再恢复，不修改仓库），CI 的 `docs-consistency` job 用它拦截未同步的文档；开发模式必须写全 `./mix dev multi|seq|stop`（**没有** `./mix seq` / `./mix multi` / `./mix stop`，README 历史版本里这三处写错）
- **内部服务令牌用 `./mix token [service]` 获取，不要再靠单测打印**：只签一枚令牌（`scripts/tools/internal-token.py`，只依赖 Python 标准库，密钥取各服务 `.env` 的 `INTERNAL_TOKEN_SECRET`）；不传服务时随机挑一个（四服务密钥一致、当前没有接口校验 `serviceName`，一枚通用），可选 `--user-id`（默认 -1）、`--ttl`（默认 24h）、`--header`、`--quiet`、`--json`、`--no-apifox`、`--dry-run`；**请求头必须带 Bearer 前缀**（`X-Internal-Token: Bearer <token>`），四个服务都会剥掉前缀再校验，漏掉会返回 401
- **`./mix token` 同时写 Apifox 变量（根目录 `.env` 配好 `APIFOX_ACCESS_TOKEN` / `APIFOX_PROJECT_ID` 时）**：默认 `apifox variables set --scope global` 写项目全局变量 `internal_token`（`--variable-name` 可改）并回读校验，Apifox 全局参数配 `X-Internal-Token: Bearer {{internal_token}}`（变量值不含 Bearer 前缀，前缀写在参数值里）；`--variable-scope environment` 时改写环境变量，**此时必须先用 `apifox export --format apifox` 回读已有 variables 再增量合并**：`environment get` / `list` 都不返回 `variables` 字段，直接 PUT 会把手工维护的变量清掉
- `scripts/dev/run.sh` 的运行工具默认值：`--java-build` 默认 `maven`、`--node-runtime` 默认 `bun`、`--python-runtime` 默认 `uv`
- 两套容器编排的容器名不同：`./mix docker` 用 `mix-<service>-container`，`./mix compose` 用 `mix-<service>`（compose 的 `container_name`）
- `README.md` 行尾由 `.gitattributes` 统一为 LF，批量改文档按「归一化 LF → 断言唯一性后替换」处理，不要逐处手工编辑
- **数据库初始化脚本**统一放根目录 `db/<类型>/`（`mysql`、`postgresql`、`clickhouse`、`mongodb`、`es`、`neo4j`），只放表、扩展、索引、集合级别的脚本；`CREATE DATABASE` 与 `USE` 一律由使用方按需自行执行，**不在脚本中写死库名**，库名以各服务的数据库配置项为准（`DB_NAME`、`DB_MYSQL_DBNAME`、`DB_DATABASE`、`DB_MYSQL_DATABASE`、`DB_POSTGRES_DATABASE`、`DB_MONGODB_DATABASE`）。PostgreSQL 容器侧的初始库由 `scripts/docker/docker-services.sh` 的 `POSTGRES_DB` 创建，需与 `DB_POSTGRES_DATABASE` 保持一致
- 技能包（`skills/` 下的 `mix-*` 目录，每个目录名与自身 SKILL.md 的 `name` 一致）改完后用 `./mix skills` 同步到本机 Agent 技能目录：脚本遍历所有 `mix-*` 技能逐个校验并镜像覆盖；目标清单在 `scripts/tools/skills-targets.conf`（只列用户级 `<home>` 技能目录，可自行追加工具，仓库内项目级目录不参与），只同步技能根目录已存在的目标，内容一致时跳过；`--list` 看检测结果、`--dry-run` 预演，脚本为 `scripts/tools/skills-sync.sh`（Windows 在 Git Bash 下执行）。脚本用 `HOME`（无则 `USERPROFILE`）解析清单里的 `<home>`，因此在 WSL 的 bash 里执行会把技能写到 Linux 侧主目录 `/home/<user>`，而 IDE 读的是 `C:\Users\<user>`，看起来「同步成功」但技能并未更新（同样是 Windows + WSL 才有的问题）；Windows 下统一用 Git Bash 执行；不要在 WSL bash 中调用，除非先显式设置 `HOME=/mnt/c/Users/<user>`
