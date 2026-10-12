# 01 阿里云 ECS 云服务器选购与系统环境初始化 SOP

> **适用场景**：指导从未购买过云服务器的小白学生，从阿里云控制台选型下单、网络安全组配置，到使用 SSH 登录并执行生产底座初始化。

---

## 一、阿里云 ECS 云服务器选购指南（避坑指南）

打开 [阿里云官网 ECS 控制台](https://ecs.console.aliyun.com/) 或 [轻量应用服务器选购页](https://swas.console.aliyun.com/)，在选购页面按以下标准勾选：

### 1.1 关键硬件参数选型推荐

| 选型维度 | 小白自学 / 课程演示推荐 | 商业生产标准推荐 | 避坑警示 |
| :--- | :--- | :--- | :--- |
| **计费方式** | **包年包月**（学生机有特惠）或 **按量付费** | 包年包月 | 演示用可买按量付费（用 2 小时花 2 块钱，用完释放） |
| **地域（Region）**| 离自己最近（如华东1 杭州、华北2 北京） | 目标用户集中区域 | 备案要求：若有域名需按所在地域提交 ICP 备案 |
| **实例规格** | **2 核 CPU，4GB 内存**（如算力型 `e` / 共享型 `s6`） | **4 核 CPU，8GB 或 16GB 内存**（计算型 `c7` / 通用型 `g7`） | ⚠️ **坚决不要买 1 核 1G 或 1 核 2G！** 运行 npm build 和 Docker 会直接爆内存死机！ |
| **操作系统镜像** | **Ubuntu 22.04 64位 LTS** | **Ubuntu 22.04 64位 LTS** 或 Alibaba Cloud Linux 3 | ⚠️ **不要选 CentOS 7**（官方已停止维护），**不要选 Windows Server**（耗费 3G 内存且性能差）。 |
| **系统盘大小** | **60 GB ~ 80 GB ESSD AutoPL** | 100 GB+ ESSD PL1 | 默认 40G 很快会被 Docker 镜像和构建缓存占满，建议至少 60G。 |
| **网络带宽模式** | **按使用流量计费（峰值 100 Mbps）** | 按固定带宽（5~10 Mbps）或按流量计费 | ⚠️ **重大省钱技巧**：选择「按使用流量」，峰值直接拉满到 100M，加载网页飞快，1G 流量仅 0.8 元；若选固定 5M，一个月要多花近百元且速度卡顿！ |

---

## 二、安全组端口放行配置（99% 新手连不上的根因）

购买完成后，进入 **ECS 实例列表** -> 点击实例名称 -> **网络与安全组** -> **安全组配置** -> 点击「**配置规则**」->「**入方向**」添加以下端口：

```
[外部互联网流量] ──► [阿里云虚拟防火墙 (安全组)] ──► 放行通过 ──► [ECS Linux 系统]
```

### 入方向必须添加的规则清单：

| 授权策略 | 协议类型 | 端口范围 | 授权对象 | 作用说明 |
| :--- | :--- | :--- | :--- | :--- |
| **允许** | TCP | **22** | `0.0.0.0/0` | SSH 终端连接（PuTTY / Xshell / VS Code） |
| **允许** | TCP | **80** | `0.0.0.0/0` | HTTP 网页标准端口 |
| **允许** | TCP | **443** | `0.0.0.0/0` | HTTPS 加密证书网页端口 |
| **允许** | TCP | **8002** | `0.0.0.0/0` | FastAPI 后端服务端口（用于前期不经过网关直连调试） |
| **允许** | TCP | **9000** | `0.0.0.0/0` | MinIO 对象存储 S3 API 接口 |
| **允许** | TCP | **9001** | `0.0.0.0/0` | MinIO 可视化管理后台控制台 |
| **严禁暴露**| TCP | 5432, 6379 | - | **PostgreSQL 与 Redis 严禁对公网开放！** 否则几分钟内就会被黑客全网勒索扫描锁定！仅限 127.0.0.1 内部访问！ |

---

## 三、首次 SSH 远程登录连接

在 Windows 电脑上打开 **PowerShell** 或 **CMD**（或使用 FinalShell / Xshell）：

```bash
# 语法：ssh root@<你的阿里云公网IP>
ssh root@123.56.78.90

# 首次连接会提示：Are you sure you want to continue connecting (yes/no/[fingerprint])?
# 输入 yes 并回车，然后输入你在阿里云设置的 root 登录密码（输入时屏幕不显示字符是正常现象）
```

看到如下终端欢迎提示即代表成功登入云端服务器：
```text
Welcome to Ubuntu 22.04.4 LTS (GNU/Linux 5.15.0-105-generic x86_64)
root@aliyun-server:~#
```

---

## 四、生产环境底层系统优化与一键脚本

针对刚买到的空白 Ubuntu 实例，必须做 **4 项关键优化**：
1. **时区校准**：同步为北京时间（`Asia/Shanghai`），否则生成的任务日志时间与本地错位 8 小时；
2. **挂载 Swap 虚拟交换内存（防 OOM 神器）**：当学生运行 `npm run build` 或高并发任务时，小内存服务器极易因瞬间爆内存被 Linux 内核 `oom-killer` 强行杀死 Python 进程。创建 4GB Swap 虚拟内存可保障系统绝不崩溃！
3. **更换国内源**：换为阿里云内网/公网高速 APT 软件源，装包飞速；
4. **提升最大打开文件数 (ulimit)**：避免高并发 WebSocket 出现 `Too many open files` 异常。

### 一键执行脚本命令：

登录服务器后，直接复制并粘贴执行以下整段初始化脚本：

```bash
curl -fsSL https://gitee.com/your-repo/raw/master/docs/bushu/scripts/init_ecs_server.sh | bash
# 或直接手动粘贴执行以下生产初始化命令：
```

```bash
#!/bin/bash
# ==============================================================================
# 阿里云 ECS 生产环境底座一键初始化脚本
# ==============================================================================
set -e

echo ">>> [1/5] 校准服务器时区为 Asia/Shanghai..."
timedatectl set-timezone Asia/Shanghai

echo ">>> [2/5] 开启 4GB Swap 虚拟交换内存 (防止内存溢出崩溃)..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap 虚拟内存配置完成 (4GB)！"
else
    echo "Swap 虚拟内存已存在，跳过创建。"
fi

echo ">>> [3/5] 优化 Linux 系统内核句柄限制..."
cat >> /etc/security/limits.conf << EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF
sysctl -p || true

echo ">>> [4/5] 更新基础工具链与构建依赖..."
apt update && apt install -y curl wget git vim htop unzip jq build-essential

echo ">>> [5/5] 安装 Docker 与 Docker Compose 插件..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
    systemctl enable --now docker
fi

echo "=================================================================="
echo "🎉 阿里云 ECS 生产环境底座初始化成功！"
echo "当前内存与 Swap 状态："
free -h
echo "=================================================================="
```

运行完成后，服务器底座就已经达到了工业级生产就绪状态！接下来即可进行代码打包与部署。
