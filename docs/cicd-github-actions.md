# CI/CD 操作指南（GitHub Actions + WSL 自托管部署）

> 适用范围：`mix-web-demo` 单仓库四服务（spring / gozero / nestjs / fastapi）+ APISIX 网关。
> 生产环境：WSL2 内网（可出站 443，无入站），仓库克隆于 `/home/hongch666/mix-web-demo`。
> 文档版本：2026-11-07。

---

## 1. 架构总览

```
┌──────────────────────────────── 公网 ────────────────────────────────┐
│ GitHub（hongch666/mix-web-demo）                                     │
│   PR(prod) ───→ ci.yml    quality ×4 ← GitHub 托管 runner（ubuntu）   │
│   prod ─→ release.yml     build ×4 → trivy → push GHCR ← 托管 runner │
│   tag  ─→ release.yml     追加 :vX.Y.Z                               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ 仅出站 443，runner 主动长轮询拉任务
┌───────────────────────────────▼──────────── WSL 内网 ────────────────┐
│ deploy.yml → 自托管 runner（label: deploy，systemd 服务）              │
│   environment: production（人工审批）                                 │
│   同步 ~/mix-web-demo 到目标 commit → compose pull → up -d --wait     │
│   失败自动回滚到上一版本                                              │
└──────────────────────────────────────────────────────────────────────┘
```

分工原则：

| 任务                          | 跑在哪             | 说明                                                            |
| ----------------------------- | ------------------ | --------------------------------------------------------------- |
| 质量门禁（lint/compile/test） | GitHub 托管 runner | 复用本地 `scripts/*.sh`，判据一致                               |
| 镜像构建 + trivy 扫描         | GitHub 托管 runner | 依赖 `type=gha` 缓存（Dockerfile 的 cache mount 跨 run 不保留） |
| 部署                          | WSL 自托管 runner  | 唯一能碰生产的一环，受 environment 审批保护                     |

镜像 tag 策略：

| Tag                | 含义               | 用途                           |
| ------------------ | ------------------ | ------------------------------ |
| `<短 sha>`（7 位） | 与 commit 一一对应 | **唯一真相**，部署与回滚只用它 |
| `latest`           | 跟随 prod          | 开发兜底                       |
| `vX.Y.Z`           | 正式版本           | 打 tag + GitHub Release 时产生 |

---

## 2. 仓库内文件清单

| 文件                                     | 作用                                                                                          |
| ---------------------------------------- | --------------------------------------------------------------------------------------------- |
| `.github/workflows/ci.yml`               | PR 质量门禁（仅 prod）：路径过滤 + 4 语言矩阵，跑 `lint.sh → compile.sh → test.sh`            |
| `.github/workflows/release.yml`          | 构建镜像（buildx + gha 缓存）→ trivy 扫描 → 推送 GHCR（跟随 `prod` 分支与 tag）               |
| `.github/workflows/deploy.yml`           | 生产部署（`Release Images` 在 prod 成功后触发）：审批、版本互斥、失败自动回滚、网关配置热重启 |
| `.github/workflows/smoke.yml`            | runner 冒烟检查（不碰容器），首次接入时验证                                                   |
| `scripts/test.sh` `lint.sh` `compile.sh` | 新增 `CI_STRICT=1`：CI 上工具缺失从「跳过」升级为「失败」                                     |
| `scripts/build.sh`                       | Spring 打包统一优先 Maven（与 Dockerfile/门禁一致），兼容 `target/` 产物                      |
| `docker-compose.yml`                     | 镜像 tag 参数化：`${DOCKER_IMAGE_TAG:-latest}`                                                |
| `.gitignore`                             | 放行 `.github/workflows/`                                                                     |
| `.env.example`                           | 更新 `DOCKER_IMAGE_TAG` 说明（compose 现在也读取它）                                          |

关键设计点：

- `ci.yml` 用 `dorny/paths-filter` 只跑改动过的服务，未变更服务不占 job。
- `deploy.yml` **不使用** `actions/checkout`，而是操作固定目录 `DEPLOY_DIR`（`~/mix-web-demo`），
  因为 `.env` 与 `.env.docker` 被 gitignore，只有宿主机克隆里才有；`git reset --hard` 不会动这些文件。
- 部署状态（上一版本 tag/commit）存在 runner 工作区之外的 `~/actions-runner/_work/mix-deploy-state/last-deploy`，
  供回滚使用。

---

## 3. GitHub 侧配置（一次性）

### 3.1 Variables

`Settings → Secrets and variables → Actions → Variables`：

| Name | Value |
| --- | --- |
| `DOCKER_IMAGE_PREFIX` | `ghcr.io/hongch666/mix-web-demo/`（必须小写、以 `/` 结尾） |
| `DEPLOY_DIR` | `/home/hongch666/mix-web-demo` |

> `DOCKER_REGISTRY` 已不再使用（GHCR 域名固定为 `ghcr.io`），可以删除该变量。

### 3.2 Secrets

`Settings → Secrets and variables → Actions → Secrets`：

镜像仓库已切换为 **GHCR**（GitHub Container Registry），推送与拉取都使用内置 `GITHUB_TOKEN`，
**无需任何自定义 Secret**（`release.yml` 声明 `packages: write`，`deploy.yml` 声明 `packages: read`）。

> 历史说明：早期版本使用阿里云 ACR 个人版，但已实测 GitHub 托管 runner 的海外出口 IP 会被 ACR 拒绝
> （`/v2/` 探针返回 401，凭据指纹校验一致，`docker login` 仍返回 400），故切换到 GHCR。

### 3.3 Environment（必须名为 `production`）

`Settings → Environments → New environment`：

1. 名称：`production`
2. 勾选 **Required reviewers**，添加审批人（部署前需网页批准）
3. 可选：Wait timer

> 不创建 environment 也能跑，但会失去审批环节。

### 3.4 分支保护（prod）

`main` 是开发分支，不触发 CI/CD；`prod` 是生产分支，必须加保护规则：

`Settings → Branches → Add branch protection rule`（Branch name pattern 填 `prod`）：

- ✅ Require a pull request before merging
- ✅ Require status checks to pass → 选中 `Quality / spring`、`Quality / gozero`、`Quality / nestjs`、`Quality / fastapi`
- ✅ Require branches to be up to date before merging

### 3.5 提交改造代码并创建 prod 分支

```powershell
git add .github/workflows .gitignore scripts docker-compose.yml .env.example docs/cicd-github-actions.md
git commit -m "ci: 接入 GitHub Actions 质量门禁、镜像发布与 WSL 自托管部署"
git push origin main

# 从 main 创建 prod 分支，作为 WSL 生产的部署来源
git push origin main:prod
```

> 说明：本仓库 origin 配置了多个 push 远端（gitee/gitlab/gitcode），CI 只在 GitHub 触发，其它远端仅作镜像。

---

## 4. WSL 生产环境配置（一次性）

### 4.1 部署目录核对（已就绪）

`~/mix-web-demo` 需要满足：

- [x] git 克隆正常、remote 指向 GitHub
- [x] `.env` 含 `DOCKER_IMAGE_PREFIX`
- [x] 四个 `.env.docker` 存在（`spring/`、`gozero/app/`、`nestjs/`、`fastapi/`）
- [ ] 建议在 `.env` 追加 `HOST_UID=1000` 与 `HOST_GID=1000`（与当前用户一致时可省略）

```bash
echo -e "HOST_UID=$(id -u)\nHOST_GID=$(id -g)" >> ~/mix-web-demo/.env
```

### 4.2 安装自托管 runner

进入 WSL（PowerShell 执行 `wsl`），WSL 已启用 systemd：

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
# 版本必须 >= 2.329.0（GitHub 强制的最低注册版本），
# 到 https://github.com/actions/runner/releases 确认最新版本号后替换 URL
curl -o runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz
tar xzf runner.tar.gz
```

获取注册 token：GitHub → **Settings → Actions → Runners → New self-hosted runner → Linux**，
复制页面命令中的 `--token` 值：

```bash
cd ~/actions-runner
./config.sh --url https://github.com/hongch666/mix-web-demo \
  --token <REG_TOKEN> \
  --labels deploy
# 交互提问回车即可，labels 一步务必包含 deploy
```

注册为 systemd 服务（开机自启，WSL 启动后自动在线）：

```bash
sudo ./svc.sh install hongch666
sudo ./svc.sh start
```

验证：GitHub → Settings → Actions → Runners，应显示 `Idle` 且 labels 含 `deploy`。

### 4.3 runner 运维（建议）

```bash
# 磁盘防护：构建层堆积是自托管 runner 最常见事故
crontab -e   # 追加：
# 0 3 * * * docker image prune -af --filter until=72h
```

- runner 版本不自动升级，GitHub 强制最低版本时会全部失败，每月检查一次 releases。
- 单台 runner 是单点，起步可接受；后续可加第二台同 label，部署并发锁会自动排队。

---

## 5. 首次验证流程

1. **冒烟**：Actions → `Runner Smoke` → Run workflow。三步全绿 = runner 连通、出网正常、部署目录就绪。
2. **门禁**：推一个 feature 分支开 PR（目标 `prod`）→ 观察 4 个 `Quality / *` 检查。
3. **构建**：把代码合到 `prod` 分支 → `Release Images` 自动跑（首次无缓存 15–25 分钟，之后命中缓存变快）→ 到 GitHub 个人/仓库 **Packages** 页面确认 `mix-<svc>` 出现 `<短 sha>` tag。
4. **部署**：`Deploy` 自动触发 → 卡在 review deployments → 勾选 `production` → **Approve and deploy**。
5. **回滚演练**：Actions → `Deploy` → Run workflow → `image_tag` 填上一个短 sha。

> 注意：当前 WSL 里业务容器未运行（只有中间件），首次部署会拉起业务 4 容器 + 网关 + 可观测组件
> （Tempo/OTel/Prometheus/Loki/Promtail/Grafana，与 `./mix compose up` 行为一致）。

---

## 6. 日常操作速查

| 操作             | 方式                                                                                        |
| ---------------- | ------------------------------------------------------------------------------------------- |
| 正常发布         | 合并到 `prod`（PR 或 fast-forward）→ 审批 → 自动部署                                        |
| 发布正式版       | `git tag v1.0.0 && git push origin v1.0.0` → GitHub Releases → Draft new release → Publish  |
| 手工部署指定版本 | Actions → `Deploy` → Run workflow → `image_tag` 填短 sha 或 `vX.Y.Z`                        |
| 回滚             | 同上，`image_tag` 填上一个短 sha（上一版本记录见下方）                                      |
| 查当前部署版本   | WSL：`cat ~/actions-runner/_work/mix-deploy-state/last-deploy`（第一列 tag，第二列 commit） |
| 查容器状态       | WSL：`cd ~/mix-web-demo && docker compose ps`                                               |
| 手动补建镜像     | Actions → `Release Images` → Run workflow                                                   |
| 手动跑单服务门禁 | Actions → `CI` → Run workflow → services 填如 `spring fastapi`                              |
| 查看镜像漏洞报告 | 仓库 Security 标签页（trivy SARIF）                                                         |

失败自动回滚的行为：`deploy.yml` 在 `compose up -d --wait` 失败时，自动 checkout 上一 commit 并用上一版本 tag 重新拉起；回滚也失败则 job 红并提示人工介入。

---

## 7. 故障排查

| 现象                                | 排查点                                                                                                         |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| runner 显示 Offline                 | WSL 是否启动；`sudo ./svc.sh status`；出站 443 是否可用（`curl -I https://api.github.com`）                    |
| `Release Images` 登录失败           | GHCR 用 `GITHUB_TOKEN`，检查 workflow 是否声明 `packages: write`；`.env` 前缀须为 `ghcr.io/<owner>/<repo>/`    |
| `Deploy` 找不到提交                 | 部署目录落后：WSL 里 `cd ~/mix-web-demo && git fetch origin prod`（deploy.yml 自己也会 fetch，一般是网络问题） |
| 部署卡在 healthcheck                | WSL 里 `docker compose ps` 与 `docker compose logs <service>`；`--wait-timeout 300` 到点后自动回滚             |
| `Quality / gozero` 报 lint 版本问题 | 版本锁在 `ci.yml` 的 `env`（`GOLANGCI_LINT_VERSION` / `GOCTL_VERSION`），与本地对齐                            |
| `Quality / spring` 测试连不上中间件 | 单测需要真实 MySQL/Nacos 时，给 job 补 `services:` 容器（找 AI 加）                                            |
| trivy 阻断发布                      | Security 标签页看报告；升级基础镜像或加 `.trivyignore`（需注明理由）                                           |
| 镜像仓库换成企业版/内网 Harbor      | `release.yml` 的 `runs-on` 改为 `[self-hosted, linux, x64, builder]`，并新增一台 builder runner                |

---

## 8. 安全约定

1. 自托管 runner 绝不响应 fork PR；部署类 workflow 只监听 `push tag` / `release` / `workflow_dispatch` / `workflow_run`。
2. 部署必须经过 `production` environment 审批；审批人在 GitHub 网页操作，内网不留人工凭据。
3. `permissions` 最小化（默认 `contents: read`，仅扫描 job 需要写 Security）。
4. secrets 只从 GitHub Environment 注入，不落盘内网机器。
5. 后续加固项：action 版本从 `@v4` 锁到具体 commit SHA。
