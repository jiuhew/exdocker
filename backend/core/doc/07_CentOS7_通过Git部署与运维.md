# CentOS 7 通过 Git 部署与运维（含网络/网关、Git、环境、Docker/Compose、自启动）

适用场景：在公司内网或云主机（CentOS 7）上，通过 Git 拉取代码并用 Docker Compose 启动整套服务。

技术栈：

- 前端: React 18 + Vite + TypeScript（Node 22）
- 后端: Django 5.x + DRF（Python 3.12）
- 队列: Celery 5.x（Redis 7.4 作为 broker/result）
- 数据库: MySQL 8.4
- 反代: Nginx 1.27
- 编排: Docker Compose v2

重要说明：CentOS 7 已到生命周期末期（EOL）。若可选，建议迁移到 Rocky/AlmaLinux 8/9。以下步骤仍可在 CentOS 7 上工作，但请注意安全更新与软件源可用性。

---

## 1. 主机基础准备

### 1.1 系统更新与基础工具

```bash
sudo yum clean all && sudo yum makecache fast
sudo yum -y update
sudo yum -y install epel-release yum-utils git curl vim unzip tar wget ca-certificates
```

### 1.2 时区与时间同步

```bash
sudo timedatectl set-timezone Asia/Shanghai
sudo yum -y install chrony
sudo systemctl enable --now chronyd
chronyc sources -v
```

### 1.3 专用用户（可选）

```bash
sudo useradd -m -s /bin/bash appuser || true
sudo usermod -aG wheel appuser
```

### 1.4 SELinux 与防火墙

- 若快速打通测试环境，可暂时放宽限制；生产请按需精细化：

```bash
# 临时（当前会话）关闭 SELinux
sudo setenforce 0 || true

# 永久（需要重启）
sudo sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config

# firewalld 放行 Web 端口
sudo yum -y install firewalld
sudo systemctl enable --now firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
# 如需外网直连测试后端/前端开发端口（可选，慎重暴露）
# sudo firewall-cmd --permanent --add-port=8000/tcp
# sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

### 1.5 网络与网关设置（静态 IP 示例）

CentOS 7 常见两种方式：`ifcfg` 配置文件或 `nmcli`（NetworkManager）。以下以 `ifcfg-eth0` 为例：

```bash
sudo bash -lc 'cat >/etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
TYPE=Ethernet
BOOTPROTO=none
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=192.168.1.100
PREFIX=24
GATEWAY=192.168.1.1
DNS1=223.5.5.5
DNS2=114.114.114.114
EOF'
sudo systemctl restart network || sudo nmcli connection reload
ip addr show eth0
ip route
cat /etc/resolv.conf
```

若使用 `nmcli`：

```bash
sudo nmcli con mod eth0 ipv4.addresses 192.168.1.100/24
sudo nmcli con mod eth0 ipv4.gateway 192.168.1.1
sudo nmcli con mod eth0 ipv4.dns "223.5.5.5 114.114.114.114"
sudo nmcli con mod eth0 ipv4.method manual
sudo nmcli con up eth0
```

> 若公司内网需代理访问外网镜像/源码，请在下文 Docker 与 Git 段落配置 HTTP/HTTPS 代理与 registry mirror。

---

## 2. 安装 Docker CE 与 Compose v2

### 2.1 安装 Docker CE

```bash
sudo yum -y remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine || true
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum -y install docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
docker version | cat
```

如需镜像加速与日志旋转，创建 `/etc/docker/daemon.json`：

```bash
sudo bash -lc 'cat >/etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://registry.docker-cn.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  },
  "exec-opts": ["native.cgroupdriver=systemd"],
  "storage-driver": "overlay2"
}
EOF'
sudo systemctl restart docker
```

> 若公司代理：在 `/etc/systemd/system/docker.service.d/http-proxy.conf` 配置 `HTTP_PROXY/HTTPS_PROXY/NO_PROXY`，并 `systemctl daemon-reload && systemctl restart docker`。

### 2.2 安装 Docker Compose v2（CLI 插件）

```bash
sudo yum -y install docker-compose-plugin || true
# 若仓库无此包，可手动安装二进制：
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64" -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version | cat
```

### 2.3（可选）将当前用户加入 docker 组

```bash
sudo usermod -aG docker $USER
# 重新登录生效
```

---

## 3. 配置 Git（SSH）

```bash
sudo yum -y install git
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "you@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
# 将公钥添加到 GitHub/GitLab → SSH Keys

# 验证
ssh -T git@github.com || true
```

如需代理：

```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
# 或对特定域名设置，仅示例
# git config --global http.https://github.com.proxy http://127.0.0.1:7890
```

---

## 4. 获取代码与环境文件

推荐放置路径：`/srv/react_explore`（可自定）。

```bash
sudo mkdir -p /srv && sudo chown -R $USER:$USER /srv
cd /srv
git clone <你的仓库地址> react_explore
cd react_explore

# 复制环境文件
cp -n .env.example .env || true
vi .env
```

至少校对以下变量（示例）：

- `DEBUG=0`
- `ALLOWED_HOSTS=your.domain.com,127.0.0.1,localhost`
- `CSRF_TRUSTED_ORIGINS=https://your.domain.com`
- `SECRET_KEY=生成强随机值`
- `DB_HOST=mysql` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`
- `REDIS_URL=redis://redis:6379/0`

> 若使用自建外部 MySQL/Redis，请改为实际内网地址与账号，并在 Compose 中移除对应服务或关闭端口映射。

---

## 5. 启动（Compose）

基础启动：

```bash
cd /srv/react_explore
docker compose pull   # 如镜像已发布到仓库（可选）
docker compose build  # 本地构建
docker compose up -d
docker compose ps | cat
```

初始化：

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

验证：

- 后端：`http://<服务器IP>:8000/api/health/`
- 前端：`http://<服务器IP>:3000`（若暴露）
- 反代（若启）：`http://<服务器IP>`

日志：

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f nginx
```

清理：

```bash
docker compose down -v
```

> 生产建议仅暴露 80/443，由 Nginx 转发到后端；3000/8000 仅在内网或调试时开放。

---

## 6. 自启动（systemd 单元）

创建 `/etc/systemd/system/react-explore.service`：

```ini
[Unit]
Description=React Explore (Docker Compose)
Requires=docker.service
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/srv/react_explore
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

启用并测试：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now react-explore.service
systemctl status react-explore.service | cat
# 重启后应自动启动
sudo reboot
```

---

## 7. Nginx 与域名/证书（可选）

若使用容器内 Nginx：

- 在 `.env` 与 `nginx/conf.d/default.conf` 中配置你的域名；
- 将 80/443 映射到宿主；
- 证书可通过 `certbot`/`acme.sh` 在宿主签发后，以只读挂载方式提供给容器。

宿主直接安装 Nginx（替代容器）也可：

```bash
sudo yum -y install nginx
sudo systemctl enable --now nginx
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
# 在 nginx.conf/server 块将 /api 转发到 后端容器映射的 8000
```

---

## 8. 安全与合规要点

- 仅暴露必需端口；后端与前端开发端口避免直接对公网开放。
- `SECRET_KEY`、数据库口令使用强随机并存放在 `.env`（必要时用 Vault/密钥管理）。
- 卷数据（MySQL/Redis/媒体）定期备份：

```bash
docker run --rm -v mysql_data:/var/lib/mysql -v /backup:/backup alpine sh -lc "tar czf /backup/mysql_$(date +%F).tgz -C /var/lib mysql"
```

- 日志轮转已在 `daemon.json` 设置；可考虑接入 ELK/Promtail。
- 定期 `docker image prune -af` 清理镜像，`docker volume ls` 巡检无用卷。

---

## 9. 常见问题

- 拉取/构建超时：配置 `registry-mirrors` 或宿主代理；预先 `docker pull` 基础镜像。
- 端口被占用：`ss -lntp` 定位占用进程；调整 Compose 映射或停用冲突服务。
- MySQL 认证失败：确保使用 `cryptography`，并匹配 MySQL 8 账号/认证插件；或改为 `mysql_native_password`。
- 容器内 DNS 解析慢：在 `daemon.json` 增加 `"dns": ["223.5.5.5","114.114.114.114"]` 后重启 Docker。
- 重启后容器未起：确认 `react-explore.service` 状态与 `docker compose` 可执行路径无误。

---

## 10. 相关文档

- 《01_构建系统.md》
- 《02_Docker与文件关系.md》
- 《03_为什么没有Django命令或环境.md》
- 《04_容器内路径与文件放置.md》
- 《05_为什么宿主机能看到镜像.md》
- 《06_容器化与本地部署的安装顺序对比.md》


