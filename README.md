# React + Django + Celery + Redis + MySQL (Dockerized)

## 🎯 项目目标

这是一个**Docker学习项目**，旨在通过搭建完整的现代网页框架来掌握容器化技术。项目涵盖了从开发到生产的完整技术栈，帮助理解Docker、Docker Compose、容器编排等核心概念。

## 🚀 技术栈

### 前端

- **React 18** + **TypeScript** + **Vite 5**
- 现代化构建工具链，支持热更新和快速开发

### 后端

- **Django 5.x** + **Django REST Framework**
- **Python 3.12** 最新特性支持
- **Celery 5.x** 异步任务队列
- **Redis 7.4** 作为消息代理和结果存储

### 基础设施

- **MySQL 8.4** 关系型数据库
- **Nginx 1.27** 反向代理和静态文件服务
- **Docker Compose v2** 容器编排

## 🐳 Docker 学习要点

### 核心概念

- **容器化**：将应用及其依赖打包到独立环境中
- **镜像管理**：理解镜像构建、标签、推送等操作
- **服务编排**：通过Compose管理多容器应用
- **网络通信**：容器间通信和端口映射
- **数据持久化**：卷挂载和数据管理

### 开发 vs 生产

- **开发环境**：代码挂载、热更新、调试友好
- **生产环境**：镜像部署、健康检查、监控告警

## 🏗️ 快速开始

### 环境要求

- **Windows 11**: Docker Desktop + WSL2
- **Linux**: Docker Engine + Compose v2
- **macOS**: Docker Desktop

### 一键启动

```bash
# 1. 复制环境配置
cp .env.example .env

# 2. 构建并启动所有服务
docker compose up -d --build

# 3. 验证服务状态
docker compose ps
```

### 服务访问

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **Nginx代理**: http://localhost/
- **健康检查**: http://localhost:8000/api/health/

## 🔧 开发工作流

### 代码修改

```bash
# 代码通过卷挂载，修改后容器自动重载
# 查看实时日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 数据库操作

```bash
# 进入后端容器
docker compose exec backend sh

# 执行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

### 任务队列

```bash
# 查看Celery状态
docker compose logs -f celery

# 测试异步任务
curl "http://localhost:8000/api/common/add/?x=1&y=2"
```

## 📚 学习路径

### 第一阶段：基础概念

1. 理解Docker镜像、容器、卷的概念
2. 掌握docker-compose.yml的配置语法
3. 学会基本的容器管理命令

### 第二阶段：服务编排

1. 理解服务间的依赖关系
2. 掌握网络配置和端口映射
3. 学会数据持久化配置

### 第三阶段：生产部署

1. 学习镜像构建和优化
2. 掌握环境变量和配置管理
3. 理解健康检查和监控

### 第四阶段：高级特性

1. 学习多环境部署策略
2. 掌握CI/CD集成
3. 理解容器安全和最佳实践

## 🗂️ 项目结构

```
react_explore/
├── backend/                 # Django后端应用
│   ├── apps/               # Django应用模块
│   ├── core/               # 核心配置
│   └── Dockerfile          # 后端镜像构建
├── frontend/               # React前端应用
│   ├── src/                # 源代码
│   └── Dockerfile          # 前端镜像构建
├── docker/                 # 数据库初始化脚本
├── nginx/                  # Nginx配置
├── docker-compose.yml      # 服务编排配置
└── .env.example           # 环境变量模板
```

## 🔍 常见问题

### 构建问题

```bash
# 如果遇到BuildKit问题，关闭BuildKit
set DOCKER_BUILDKIT=0
docker compose build
```

### 端口占用

```bash
# 检查端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

### 数据重置

```bash
# 完全重置（删除所有容器和数据）
docker compose down -v
docker compose up -d --build
```

## 📖 深入学习

### 推荐资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [Django官方文档](https://docs.djangoproject.com/)
- [React官方文档](https://react.dev/)

### 进阶主题

- 容器镜像优化和分层
- 多阶段构建
- 容器安全扫描
- 性能监控和调优
- 微服务架构设计

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

感谢所有为Docker生态做出贡献的开发者和社区成员。

---

**Happy Docker Learning! 🐳✨**
