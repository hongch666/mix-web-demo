---
name: mix-docker
description: mix-web-demo 容器镜像与分发专项规范，覆盖镜像命名推送、本地优先远程兜底、FastAPI 字节码镜像与各服务 .dockerignore 边界。修改 Dockerfile/.dockerignore 或镜像发布时加载
---

# mix-docker 容器镜像与分发规范

## 容器镜像与镜像分发

### 镜像名称、推送与版本

- `./mix docker build` 产出本地镜像 `mix-<service>:latest`（只处理 spring/gozero/nestjs/fastapi；gateway 用官方 `apache/apisix` 镜像，不构建也不推送）
- `./mix docker push --prefix <前缀> [--tag <tag>] [service...]` 把本地镜像重打标签为 `<前缀>/mix-<service>:<tag>` 后推送：**不传 `--tag` 时固定推 `latest`**，脚本没有从 Git 提交号或时间推导版本的逻辑，也不读本地镜像的实际 tag；`gateway` 直接跳过，未知服务名只警告
- 推送脚本只做 `docker tag` + `docker push`，**不执行 `docker login`**：首次推送前自行登录目标仓库

### 本地构建优先、远程镜像兜底

- 统一镜像名的开关是根目录 `.env` 的 `DOCKER_IMAGE_PREFIX`，**取值必须以 `/` 结尾**（`docker.io/yourname/`、`registry.example.com/team/`）；未配置时保持纯本地模式，行为与引入该变量前完全一致
- `docker-compose.yml` 四个业务服务的镜像写 `${DOCKER_IMAGE_PREFIX:-}mix-<service>:latest`：前缀为空退化为本地名，配置后为 `<前缀>mix-<service>:latest`，与推送出去的镜像名一致
- `scripts/docker/build_and_run_services.sh` 在构建成功后按前缀补打同名标签，保证 compose 命中的就是本次本地构建结果；`scripts/docker/docker-compose-up.sh` 先按有效名检查，本地构建存在但有效名缺失时补标签，两者都缺失且配置了前缀时交给 compose 拉取，未配置前缀才走本地构建
- 生效依赖 Compose 默认的 `pull_policy: missing`：本地有同名镜像直接使用，缺失才拉取。要强制以远端为准必须显式 `pull_policy: always`，代价是每次 `up` 都拉取、本地构建结果会被同名远端镜像覆盖
- build / compose-up / push 三个脚本都会在环境变量未设置时读取根目录 `.env` 的同名变量，保持同一口径
- `./mix compose up` 的本地镜像检查发生在 compose 合并逻辑之外：纯用远端镜像时直接 `docker compose up -d` 或先 `docker compose pull`，不要依赖该脚本跳过本地构建
- 本机访问 Docker Hub 失败（`failed to fetch anonymous token`、`dial tcp` 超时）时，`docker build` 与 `docker buildx build --check` 都会停在拉取基础镜像元数据阶段，这是环境问题（未配置加速或代理），不要据此判定 Dockerfile 写法有误
- **网关的 Nacos 发现只由 worker 0 拉全量、再经 resty-events 广播给其它 worker**：`fetch_full_registry` 在节点内容未变化时直接 return，不再补发事件。多 worker 下首次广播若早于某个 worker 完成 `init_worker`，该 worker 的 `applications` 永远是 nil，它接手的请求全部 503，`logs/gateway/error.log` 里是 `failed to set upstream: no valid upstream node: nil`；`docker compose restart` 会照样复现，失败比例约等于空 worker 的占比（12 核 WSL 实测 5/6 以上 503，且错误计数每次重启后继续累加）。**根治是 `gateway/apisix/config.yaml` 的 `nginx_config.worker_processes: 1`**：键必须在 `nginx_config` 下，写成 `nginx_config.main.worker_processes` 不生效（生成后 `conf/nginx.conf` 仍是 `worker_processes auto;`），单 worker 由自己拉取、拉取失败也会在 `fetch_interval` 周期自愈；实测连续重启两次、四服务各 10 次请求全 200，业务接口从 503 变为正常 401。单 worker 吞吐只适合本地/单机 compose，生产多实例需另配。`scripts/gateway/gateway-dev.sh` 与 `scripts/docker/docker-compose-up.sh` 的 Swagger 轮询 + `restart` 仍作为启动期兜底；排查时先确认 `conf/nginx.conf` 的 worker 数，不要改 `apisix.yaml` 的 upstream 配置
- **docker compose 需 ≥ v2.36.0**：v2.35.x 在 `up` 时并发拉取镜像会 `fatal error: concurrent map writes`，栈顶在 `pkg/compose.(*composeService).pullRequiredImages`（docker/compose#12747，v2.36.0 修复）；`scripts/docker/prepull-images.sh` 在 `./mix dev seq` 启动网关前与 `./mix compose up` 前用 `docker CLI` 串行预拉缺失镜像做兜底（命中缓存即跳过、失败不阻断），根治仍是升级 compose 或临时降到 ≤ v2.27.x；遇到该崩溃先看 `docker compose version`，不要改项目编排文件

### FastAPI 镜像只保留字节码

- `fastapi/Dockerfile` 为多阶段：builder 用 `python -m venv /opt/venv` 装依赖，`compileall -b -f main.py app` 后 `find /app -name '*.py' -delete`；runtime 只复制 `/opt/venv` 与 `/app`
- `-b` 是必需项：产出与源码同目录的 `main.pyc`、`__init__.pyc`（legacy 布局），删掉 `.py` 后仍可按模块名导入；不加 `-b` 时产物落在 `__pycache__/`，删源码就无法导入
- 两个阶段必须使用同一基础镜像 tag（当前 `python:3.12-slim-bookworm`），否则字节码 magic number 与 ABI 不匹配；升级 Python 版本要两处同步改
- 仍会出现在镜像中且属预期：`application.yaml`（`load_config` 按 `Path(__file__).parents[3]` 定位，`.pyc` 与 `.py` 同目录时结果一致）、`/opt/venv` 下第三方库的 `.py`、`logs/`、`static/`
- 已知边界：`.pyc` 可被反编译（提高门槛而非绝对保护）、traceback 不再打印源码行、容器内不能开 `--reload`（热重载依赖 `.py`）
- 改依赖或包结构后正常重建即可；`requirements.txt` 只在 builder 阶段需要，runtime 已删除

### .dockerignore 约定（四个业务服务）

构建上下文是服务目录本身（`docker build` 在服务目录内执行，不是仓库根目录），只排除构建与运行都不需要的内容：

- 公共项：`.env` / `.env.docker`（运行期由 `--env-file` / `env_file` 传入）、IDE 与 OS 文件、`.git`、日志目录、本地构建产物
- `spring/`：`src/test/`（`mvn package -DskipTests` 不需要测试源码，排除后不再编译测试类）、`docs/`、`logs/`、`*.md`
- `gozero/`：`api/`、`template/`、`script/`、`**/*_test.go`、`.golangci.yml`。**禁止改成 `**/docs`**：`gozero/app/docs`的 swagger 资源由`go:embed`嵌入二进制，缺失会直接构建失败；现有根级`docs/` 只匹配上下文根目录，安全
- `nestjs/`：单测与源码同目录，必须用 `**/*.spec.ts` 覆盖 `src/**`，并用 `**/*-spec.ts` 覆盖 `*.e2e-spec.ts` / `*.integration-spec.ts`。**只写 `test/` 等于没写**（当前仓库没有该目录），`test/` 仅作后续 e2e 目录的预留；`tsconfig.build.json` 本来就 exclude `**/*spec.ts`，因此排除后不影响 `nest build`
- `fastapi/`：`tests/`、`docs/`、`script/`、`*.md`
- 匹配语义是 Go 的 `filepath.Match`：`*` 不跨 `/`，所以 `*.md` 只排除上下文根目录那一层；要按任意层级排除必须写 `**/xxx`，写之前先确认目标不是编译期或运行期依赖（gozero 的 `app/docs` 就是反例）
- 改完 `.dockerignore` 或 Dockerfile 后自检：`./mix docker build <service>`，再用 `docker run --rm --entrypoint sh mix-<service>:latest -c "ls /app"` 核对内容（fastapi 追加 `find /app -name '*.py'`，预期无输出）
