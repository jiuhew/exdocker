# Docker 与文件关系

## Compose 与服务

- `docker-compose.yml` 定义：
  - 服务：`mysql`、`redis`、`backend`、`celery`、`celery-beat`、`frontend`、`nginx`
  - 端口映射：`8000/3000/80/3306/6379`
  - 环境变量：数据库与 Redis、Celery 配置
  - 卷：代码挂载、MySQL/Redis 数据卷、静态/媒体
  - 健康检查：确保依赖顺序（MySQL/Redis 健康后再启后端/队列）

## 各文件职责

- `backend/Dockerfile`
  - 基于 `python:3.12-slim`
  - 安装 `backend/requirements.txt`
  - 复制代码并默认运行 `python manage.py runserver`
  - 同一镜像被 `backend/celery/celery-beat` 共用（不同启动命令）

- `frontend/Dockerfile`
  - 基于 `node:22-alpine`
  - 安装依赖，默认运行 `vite dev --host 0.0.0.0`

- `nginx/nginx.conf` 与 `nginx/conf.d/default.conf`
  - `/api/` 反向代理 `rx_backend:8000`
  - 根路径可返回占位或托管前端构建产物（生产）

- `docker/mysql/init.sql`
  - 首启自动执行（通过挂载到 `docker-entrypoint-initdb.d/`），创建库/设置字符集

- `.env.example` / `.env`
  - Compose 与后端读取的统一环境变量来源（数据库/Redis/Celery/调试开关）

- `backend/requirements.txt`
  - 使用 `PyMySQL + cryptography` 替代 `mysqlclient`

- `backend/core/__init__.py`
  - `pymysql.install_as_MySQLdb()` 让 Django 使用 PyMySQL 作为 MySQLdb 实现
  - 暴露 `celery_app`，Celery 自动发现任务

- `frontend/vite.config.ts`
  - 开发期将 `/api` 代理到 `http://localhost:8000`

## 服务交互（运行时）

- `mysql`、`redis` → 健康后
- `backend` 连接 `mysql:3306` 与 `redis:6379`，提供 REST API
- `celery` 消费异步任务、`celery-beat` 下发定时任务
- `frontend` 在 `3000` 端口，调用 `/api/*`
- `nginx` 统一入口（生产/集成），将 `/api` 转发到后端

## 常用命令

- 启动：`docker compose up -d`
- 查看状态：`docker compose ps`
- 进入后端容器：`docker compose exec backend sh`
- 管理命令：`docker compose exec backend python manage.py migrate`
- 清理：`docker compose down -v`
