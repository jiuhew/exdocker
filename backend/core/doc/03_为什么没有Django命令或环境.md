# 为什么本机没有 Django 命令/环境？

## 原因

本项目采用容器化开发，Django 安装在后端镜像/容器里。本机未安装 Python 包，因此本地终端/IDE 不认识 `django-admin`，也无法本地解析依赖。

## 方案A：全容器开发（不在本机装依赖）

- 常用命令：
  - 查看日志：`docker compose logs backend -f`
  - 进容器：`docker compose exec backend sh`
  - 管理命令：
    - `docker compose exec backend python manage.py migrate`
    - `docker compose exec backend python manage.py createsuperuser`
    - `docker compose exec backend python manage.py shell`

- VS Code：
  - Docker 扩展右键容器：Attach Shell / View Logs
  - 或使用 Dev Containers 扩展，直接"在容器中打开"项目

优点：环境一致；缺点：若不在容器中开发，IDE 本地智能提示可能欠佳。

## 方案B：本机建虚拟环境（增强 IDE 体验）

1. 创建并激活虚拟环境

```powershell
cd C:\workspace\react_explore
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

1. 指向容器里的数据库/Redis（通过端口映射）

- 复制 `.env.example` 为 `.env.local`，关键项改为：
  - `DB_HOST=127.0.0.1`
  - `DB_PORT=3306`
  - `REDIS_URL=redis://127.0.0.1:6379/0`
  - `CELERY_BROKER_URL=redis://127.0.0.1:6379/0`
  - `CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1`

1. 运行后端（确保 MySQL/Redis 容器已启动）

```powershell
python backend\manage.py runserver 0.0.0.0:8000
```

1. VS Code 选择解释器

- Command Palette → "Python: Select Interpreter" → 选择 `.venv`
- `python -m django --version` 有输出即表示已装好 Django

## 常见问题

- 提示 `MySQLdb` 缺失：已使用 `PyMySQL`，并在 `backend/core/__init__.py` 安装为 MySQLdb 兼容层
- 认证报错：已包含 `cryptography` 以支持 MySQL 8 的 `caching_sha2_password`
- 容器日志看不到：设置日志驱动为 `json-file` 后重建容器
