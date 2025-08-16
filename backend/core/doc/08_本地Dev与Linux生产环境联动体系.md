# 本地 Dev 与 Linux 生产环境的联动体系

目标：在保持环境一致性的前提下，形成“本地开发 → 预发/灰度 → 生产”的可控发布链路，覆盖代码、镜像、配置、数据、观测与回滚。

适用当前栈：React 18 + Vite + TS（Node 22）/ Django 5 + DRF（Python 3.12）/ Celery 5（Redis 7.4）/ MySQL 8.4 / Nginx 1.27 / Compose v2。

---

## 1. 架构与环境分层

- 环境层级：
  - Dev（本地）：开发者机器，`docker compose` + 代码挂载，快速迭代。
  - Staging（预发，可选）：与生产同构，验证变更，连隔离的数据库/Redis。
  - Prod（生产）：高可用/只读配置、观测齐备、严格变更窗口。

- 一致性原则：
  - 同一 `docker-compose.yml`，通过 `compose.override.dev.yml`（本地）与 `compose.prod.yml`（生产）做差异化覆盖。
  - 尽量相同的镜像与启动命令（`command/entrypoint`），差异通过环境变量与配置文件控制。

目录建议：

```
repo/
  docker-compose.yml                # 基线定义
  compose.override.dev.yml          # 仅本地开发使用
  compose.prod.yml                  # 生产/预发使用
  backend/Dockerfile
  frontend/Dockerfile
  .env.example
  .env.dev                         # 本地（不入库，示例放 .example）
  .env.staging                     # 预发（不入库）
  .env.prod                        # 生产（不入库）
```

---

## 2. Git 分支与版本策略

- 分支模型（示例）：
  - `main`：受保护分支，合并即构建 `:main-<shortsha>` 镜像，部署到 Staging。
  - `release/vX.Y.Z`：发布分支，稳定期后打 Tag。
  - `feature/*`：开发分支，提交 PR → CI 进行构建与测试（可选推送临时镜像）。

- 版本与镜像标签：
  - 开发态：`backend:main-<sha>`、`frontend:main-<sha>`
  - 正式版：`backend:vX.Y.Z`、`frontend:vX.Y.Z`
  - 生产仅接受 `v*` 标签部署，便于回滚。

---

## 3. 镜像与 Compose 分层

- Dev（本地）：
  - `docker compose -f docker-compose.yml -f compose.override.dev.yml up -d`
  - 覆盖：绑定挂载源码、开放 3000/8000、使用匿名卷持有 `node_modules`、可启用热更新。

- Staging/Prod：
  - `docker compose -f docker-compose.yml -f compose.prod.yml up -d`
  - 覆盖：禁用源码挂载，仅用镜像；关闭开发端口；通过 Nginx 暴露 80/443；只读配置挂载；严格健康检查与重启策略。

compose 覆盖关键点：

- backend/celery/celery-beat：同一镜像，不同 `command`。
- volumes：Dev 绑定源码；Prod 使用命名卷（仅静态/媒体/数据）。
- env_file：Dev 用 `.env.dev`，Prod 用 `.env.prod`。

---

## 4. CI/CD 基线流程

流水线阶段：

1) 检查与测试：Lint/Unit/集成测试。
2) 构建镜像：前后端分别构建，打 `main-<sha>` 或 `vX.Y.Z` 标签，推送至私有 Registry。
3) 安全扫描：依赖与镜像漏洞扫描（可选）。
4) 部署：
   - Staging：合并到 `main` 自动部署到预发。
   - Prod：创建 Release Tag 触发生产部署（需人工批准）。

部署执行（两种常见方式）：

- 方式A：CI 通过 SSH 登录目标机，执行 `docker compose pull && docker compose up -d`。
- 方式B：目标机跑一个 `watcher`/Webhook，接收 CI 通知后执行部署脚本。

关键文件（示例片段）：

```yaml
# .github/workflows/deploy.yaml（摘要）
on:
  push:
    branches: [ main ]
  push:
    tags: [ 'v*' ]

jobs:
  build-and-push:
    steps:
      - uses: actions/checkout@v4
      - name: Build backend
        run: docker build -t registry/app-backend:${{ github.ref_name }}-${{ github.sha }} backend
      - name: Build frontend
        run: docker build -t registry/app-frontend:${{ github.ref_name }}-${{ github.sha }} frontend
      - name: Push
        run: |
          docker push registry/app-backend:...
          docker push registry/app-frontend:...
  deploy:
    needs: build-and-push
    if: startsWith(github.ref, 'refs/tags/v') || github.ref == 'refs/heads/main'
    steps:
      - name: SSH deploy
        run: ssh user@server 'cd /srv/react_explore && ./deploy.sh $TAG'
```

`deploy.sh`（服务器侧，摘要）：

```bash
#!/usr/bin/env bash
set -euo pipefail
TAG="$1"                      # main-<sha> 或 vX.Y.Z
export COMPOSE_FILE=docker-compose.yml:compose.prod.yml
export TAG="$TAG"
docker compose pull || true    # 如使用远端镜像
docker compose up -d
docker compose ps
```

> 通过 `compose.prod.yml` 中的 `image: registry/app-backend:${TAG}` 方式实现按标签部署。

---

## 5. 配置与密钥

- `.env.*` 不入库；用 `.env.example` 提示变量。
- CI 使用平台 Secrets 注入构建与部署所需的账号/令牌；服务器 `.env.prod` 仅宿主管理。
- 生产建议接入专用密钥管理（Vault/参数服务），容器以只读方式加载。

---

## 6. 数据库、迁移与任务队列

- 数据库：
  - Dev 使用独立实例或容器；严禁连接 Prod 实例。
  - Staging 从 Prod 匿名化/脱敏备份恢复，验证迁移与长事务。
  - Prod 部署前执行 `python manage.py migrate`，有破坏性变更需灰度或分两步迁移。

- 迁移策略：
  - 首先在 Dev/Staging 跑迁移并执行回归测试。
  - 生产迁移与应用重启同一窗口完成，或先迁移再切流量。

- Celery/Redis：
  - 不同环境使用不同 Redis 实例或不同前缀/DB；避免跨环境队列污染。
  - 任务幂等（消费失败可重试）。

---

## 7. 静态与媒体

- 静态资源（Django collectstatic/前端构建产物）：
  - Prod：镜像内带静态或在启动时 `collectstatic` 到命名卷，由 Nginx 提供。
  - Dev：本地卷或直接由 Vite dev server 提供。

- 媒体（用户上传）：
  - 生产建议使用对象存储（S3/OSS/MinIO）。
  - Dev/Staging 可用 MinIO 以保持一致，或周期性从 Prod 同步到 Staging（脱敏/只读）。

---

## 8. 发布策略与回滚

- 蓝绿发布：
  - 维护两套 Compose Stack（A/B），镜像与配置相同；Nginx 反代在 A/B 之间切换 upstream。
  - 回滚：切回上一套（秒级）。

- 金丝雀发布：
  - 同时运行旧/新后端，Nginx 配置按权重转发 5%/20%/100%。

Nginx 片段（摘要）：

```nginx
upstream backend_pool {
    server 127.0.0.1:18000 weight=95;   # 旧
    server 127.0.0.1:28000 weight=5;    # 新
}
location /api/ {
    proxy_pass http://backend_pool;
}
```

回滚清单：

1) 快速切回上一个镜像标签 `vX.Y.Z-1`；
2) 如涉及迁移，需准备向后兼容或回滚脚本；
3) 确认队列中任务与版本兼容。

---

## 9. 观测与告警

- 日志：`docker logs` 仅供排障；生产接入集中式日志（Loki/ELK）。日志中带 `env=prod/staging/dev` 字段。
- 指标：Prometheus + Grafana，关注延迟、错误率、资源使用、队列堆积、DB 连接等。
- APM/错误上报：Sentry/OpenTelemetry，在 `settings` 中按环境上报。

---

## 10. 联通与边界

- Dev 访问 Staging/Prod 的必要场景：
  - 仅通过受控入口（VPN/WireGuard/零信任或堡垒机），禁止直连数据库与队列。
  - 临时联调可用反向 SSH 隧道或内网穿透，但必须最小权限、限时、审计。

- 跨环境链接：
  - 禁止 Dev 直接写入 Prod 的 Redis/MySQL。
  - 媒体/只读副本可采用定时同步至 Staging，并做脱敏。

---

## 11. 操作清单（落地速查）

- 本地：
  - `.env.dev` → `docker compose -f docker-compose.yml -f compose.override.dev.yml up -d`
  - 代码改动 → 本地验证 → PR → 合并 main

- 预发：
  - 合并 `main` 触发 CI：构建 `:main-<sha>` → 部署 Staging
  - 验证健康、迁移与关键用例

- 生产：
  - 创建 Tag `vX.Y.Z` → CI 构建/推送 → 人工批准 → 部署 Prod
  - 观测窗口：10~30 分钟；若异常，按回滚清单执行

---

## 12. 相关文档

- 《01_构建系统.md》
- 《06_容器化与本地部署的安装顺序对比.md》
- 《07_CentOS7_通过Git部署与运维.md》



## 13. 容器与宿主依赖边界（FAQ）

- 结论：容器把用户态运行时与依赖（Node/Python/包管理器等）搬进镜像/容器中，通常不再需要在宿主机安装这些软件；但并非“完全不依赖宿主”。容器仍依赖宿主内核、CPU 架构、网络/防火墙、cgroups、存储驱动等底层能力。

### 能做到的

- 在 CentOS 7 上运行新版 Node 22：可行。

```bash
docker run --rm node:22-alpine node -v
```

- 避开宿主用户态限制：即使宿主无法通过系统包管理器安装 Node/Python，新版用户态环境也能随镜像使用。
- 复用同一镜像到 Dev/Staging/Prod：环境一致更可控。

### 仍受宿主限制的地方

- 内核与容器运行时：依赖宿主内核与 Docker/Containerd。CentOS 7（3.x 内核）可跑常见工作负载，但对 cgroup v2、eBPF、nftables 等新特性支持有限。
- CPU 架构：宿主是 x86_64 就使用 x86_64 镜像；arm64 需多架构镜像或 qemu（可能有性能损失）。
- 驱动类能力：GPU/高性能 NIC/USB 等需要宿主安装驱动，并将设备透传给容器。
- 网络与防火墙：端口映射依赖宿主 iptables/firewalld；策略与占用会影响容器暴露端口。
- 存储与文件系统：overlay2 等需要宿主支持；卷数据存于宿主磁盘，权限/SELinux 生效。
- 资源与安全沙箱：cgroups/capabilities/seccomp/apparmor/SELinux 由宿主提供并约束。

### 在 CentOS 7 跑新版 Node 的实操建议

- 使用官方镜像（Debian/Alpine）：`node:22` 或 `node:22-alpine`。
- 宿主检查：

```bash
docker version | cat
uname -r
docker info | grep -E 'Storage Driver|Cgroup'
iptables -V
```

- 典型问题与规避：
  - overlay2 不可用 → 更新 Docker CE、启用 overlay2 或升级内核/系统。
  - 拉取慢/超时 → 配置 registry mirror 或代理。
  - 端口/防火墙 → 放行 80/443，避免直接把 3000/8000 暴露公网。
  - 架构不匹配 → 选用多架构镜像（linux/amd64 或 linux/arm64），必要时启用 qemu。

### 一句话理解

- 是：可以通过 Docker 在 CentOS 7 使用“宿主装不了”的用户态软件（如 Node 22）。
- 但不是完全无依赖：容器仍“骑在”宿主内核和硬件之上，内核/网络/存储/安全等底层条件必须满足。若条件允许，生产建议采用更现代的发行版（Rocky/AlmaLinux 8/9）。
