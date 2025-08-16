# 文档索引（backend/core/doc）

- 01_构建系统.md：从零到一构建与启动、常见问题规避
- 02_Docker与文件关系.md：Compose/镜像/容器与配置文件的对应关系
- 03_为什么没有Django命令或环境.md：原因与两种开发方式（容器内/本地虚拟环境）
- 04_容器内路径与文件放置.md：各服务在容器内的落位、挂载与验证
  - 05_为什么宿主机能看到镜像.md：镜像/容器/进程的区别与验证方式
  - 06_容器化与本地部署的安装顺序对比.md：本地 vs 容器的安装顺序与差异
  - 07_CentOS7_通过Git部署与运维.md：在 CentOS 7 上的 Git 拉取、网络/网关、环境、Docker/Compose、自启动与安全
  - 08_本地Dev与Linux生产环境联动体系.md：Dev/Staging/Prod 分层、分支与版本、CI/CD、配置密钥、发布与回滚

## 快速导航

- 启动（首次/变更）：

```bat
docker compose build
docker compose up -d
```

- 查看状态与日志：

```bat
docker compose ps
docker compose logs backend -f
```

- 进入容器：

```bat
docker compose exec backend sh
```

- 管理命令：

```bat
docker compose exec backend python manage.py migrate
```
