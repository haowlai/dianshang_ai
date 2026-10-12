# 05 CI/CD 自动化打包与持续部署实战（GitHub Actions & 阿里云云效）

> **核心目标**：彻底告别“手动打包、手动传文件、手动重启服务器”的原始操作。实现：**只要开发者将经过测试的代码合并（Merge）到 `prd` 生产分支，CI/CD 流水线就会在云端自动编译、自动打包镜像、推送到阿里云容器仓库，并自动连上生产服务器完成零停机发布与钉钉通知**！

---

## 目录
- [一、CI/CD 自动化流水线架构与流转时序](#一cicd-自动化流水线架构与流转时序)
- [二、准备工作：开通阿里云容器镜像服务 (ACR 免费版)](#二准备工作开通阿里云容器镜像服务-acr-免费版)
  - [2.1 创建个人版实例与命名空间](#21-创建个人版实例与命名空间)
  - [2.2 创建后端与前端镜像仓库](#22-创建后端与前端镜像仓库)
  - [2.3 设置独立访问凭证密码](#23-设置独立访问凭证密码)
- [三、GitHub Actions 自动化流水线实战配置](#三github-actions-自动化流水线实战配置)
  - [3.1 在 GitHub 仓库配置 Secrets 敏感变量](#31-在-github-仓库配置-secrets-敏感变量)
  - [3.2 编写生产级发布工作流 (.github/workflows/deploy-prd.yml)](#32-编写生产级发布工作流-githubworkflowsdeploy-prdyml)
- [四、备选方案：阿里云云效 (Apsara DevOps) 国内极速流水线](#四备选方案阿里云云效-apsara-devops-国内极速流水线)
- [五、学生团队开发实战演练：从发 PR 到全自动上线](#五学生团队开发实战演练从发-pr-到全自动上线)

---

## 一、CI/CD 自动化流水线架构与流转时序

```mermaid
sequenceDiagram
    autonumber
    actor Dev as 开发者 / 学生
    participant GitHub as GitHub 仓库 (prd 分支)
    participant Action as GitHub Actions Runner
    participant ACR as 阿里云容器镜像服务 ACR
    participant ECS as 阿里云 ECS 生产服务器
    participant Ding as 钉钉 / 飞书团队群

    Dev->>GitHub: 提交 Pull Request 并合并至 prd 分支
    GitHub->>Action: 自动触发 deploy-prd.yml 流水线
    
    activate Action
    Action->>Action: 1. 拉取代码，安装 Node 编译前端生成 dist/
    Action->>Action: 2. 构建 backend & frontend 生产镜像
    Action->>ACR: 3. docker push 推送镜像至阿里云 ACR
    Action->>ECS: 4. SSH 免密登录服务器执行部署命令
    deactivate Action

    activate ECS
    ECS->>ACR: 5. docker pull 拉取最新镜像
    ECS->>ECS: 6. docker compose up -d 滚动平滑更新业务容器
    ECS->>ECS: 7. 执行 curl /health 健康检查验证
    ECS-->>Action: 8. 返回执行结果状态
    deactivate ECS

    Action->>Ding: 9. 推送构建通知："版本 v1.0.x 生产发布成功！"
```

---

## 二、准备工作：开通阿里云容器镜像服务 (ACR 免费版)

阿里云提供了面向个人的**容器镜像服务 ACR（个人版）**，提供免费的私有镜像托管配额，速度极快（国内下载速度高达数十 MB/s）。

### 2.1 创建个人版实例与命名空间
1. 登录 [阿里云 ACR 控制台](https://cr.console.aliyun.com/)；
2. 选择地域（建议选择与你的 ECS 服务器相同地域，如 `华东1 (杭州)`，内网拉取镜像完全免费且速度极快）；
3. 点击「**创建个人版实例**」；
4. 点击左侧「**命名空间**」->「**创建命名空间**」，输入一个全局唯一的名字（例如 `agentic-commerce-prd`），访问级别选择 **私有**。

---

### 2.2 创建后端与前端镜像仓库
进入左侧「**镜像仓库**」-> 点击「**创建镜像仓库**」：
1. **后端仓库**：
   - 仓库名称：`agentic-backend`
   - 仓库类型：私有
   - 代码源：选择本地仓库即可。
2. **前端仓库**：
   - 仓库名称：`agentic-frontend`
   - 仓库类型：私有。

创建完成后，页面会给出你的私有公网 Registry 地址，例如：
`registry.cn-hangzhou.aliyuncs.com/agentic-commerce-prd/agentic-backend`

---

### 2.3 设置独立访问凭证密码
在左侧菜单点击「**访问凭证**」->「**设置固定密码**」，输入一个独立的镜像拉取/推送密码（这个密码将用于 CI/CD 流水线登录认证）。

---

## 三、GitHub Actions 自动化流水线实战配置

### 3.1 在 GitHub 仓库配置 Secrets 敏感变量

在你的 GitHub 项目主页 -> 点击 **Settings** -> 左侧 **Secrets and variables** -> **Actions** -> 点击 **New repository secret**，添加以下 5 个私密变量：

| Secret 变量名 | 变量值示例 | 说明 |
| :--- | :--- | :--- |
| `ALIYUN_REGISTRY` | `registry.cn-hangzhou.aliyuncs.com` | 阿里云镜像服务注册中心域名 |
| `ALIYUN_NAMESPACE`| `agentic-commerce-prd` | 你的 ACR 命名空间 |
| `ALIYUN_USERNAME` | `13800138000` 或 `your_aliyun_account` | 阿里云主账号用户名 |
| `ALIYUN_PASSWORD` | `YourAcrStrongPassword2026!` | 刚才在 ACR 访问凭证里设置的固定密码 |
| `SERVER_HOST` | `123.56.78.90` | 阿里云 ECS 的公网 IP 地址 |
| `SERVER_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | 登录服务器的 SSH 私钥文本 |
| `DINGTALK_WEBHOOK`| `https://oapi.dingtalk.com/robot/send?...` | （可选）钉钉机器人 Webhook 地址 |

---

### 3.2 编写生产级发布工作流 (.github/workflows/deploy-prd.yml)

在代码仓库根目录创建 `.github/workflows/deploy-prd.yml` 文件：

```yaml
name: Production Release CI/CD (prd)

# 仅在代码合并推送到 prd 分支时触发
on:
  push:
    branches:
      - prd

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      # ── 1. 检出代码 ──
      - name: Checkout Code
        uses: actions/checkout@v4

      # ── 2. 生成基于 Git Commit 的唯一版本号 ──
      - name: Generate Version Tag
        id: vars
        run: echo "SHA_SHORT=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT

      # ── 3. 登录阿里云容器镜像服务 (ACR) ──
      - name: Login to Aliyun ACR
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.ALIYUN_REGISTRY }}
          username: ${{ secrets.ALIYUN_USERNAME }}
          password: ${{ secrets.ALIYUN_PASSWORD }}

      # ── 4. 构建并推送后端镜像 ──
      - name: Build and Push Backend Image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-backend:${{ steps.vars.outputs.SHA_SHORT }}
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-backend:latest

      # ── 5. 构建并推送前端镜像 ──
      - name: Build and Push Frontend Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          push: true
          tags: |
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-frontend:${{ steps.vars.outputs.SHA_SHORT }}
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-frontend:latest

      # ── 6. 远程 SSH 连接阿里云 ECS 并执行平滑升级 ──
      - name: Deploy to Aliyun ECS via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: root
          key: ${{ secrets.SERVER_SSH_KEY }}
          script_stop: true
          script: |
            echo ">>> [1/4] 登录服务器，准备拉取最新镜像..."
            cd /data/docker-deploy
            
            # 登录 ACR
            docker login --username=${{ secrets.ALIYUN_USERNAME }} --password=${{ secrets.ALIYUN_PASSWORD }} ${{ secrets.ALIYUN_REGISTRY }}
            
            echo ">>> [2/4] 拉取最新镜像版本: ${{ steps.vars.outputs.SHA_SHORT }}..."
            docker pull ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-backend:latest
            docker pull ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-frontend:latest
            
            echo ">>> [3/4] 平滑滚动重启业务容器 (DB与Redis保持连接)..."
            docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
            
            echo ">>> [4/4] 运行数据库增量初始化与健康探针..."
            docker compose -f docker-compose.prod.yml exec -T backend python -m app.scripts.init_db
            
            # 等待 3 秒探活
            sleep 3
            HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/health)
            if [ "$HEALTH_CODE" != "200" ]; then
                echo "🚨 健康检查失败！HTTP 状态码: $HEALTH_CODE"
                exit 1
            fi
            
            # 清理历史悬空旧镜像，释放磁盘空间
            docker image prune -f
            echo "🎉 生产发布圆满成功！版本号: ${{ steps.vars.outputs.SHA_SHORT }}"

      # ── 7. 发送钉钉群通知 (可选) ──
      - name: DingTalk Notification
        if: always()
        run: |
          STATUS="${{ job.status }}"
          COLOR="green"
          if [ "$STATUS" != "success" ]; then COLOR="red"; fi
          curl -s -H "Content-Type: application/json" \
            -d "{\"msgtype\":\"markdown\",\"markdown\":{\"title\":\"生产发布报告\",\"text\":\"### 🚀 AgenticCommerce 生产发布通知\n- **分支**: prd\n- **版本**: ${{ steps.vars.outputs.SHA_SHORT }}\n- **发布状态**: $STATUS\n- **操作人**: ${{ github.actor }}\"}}" \
            "${{ secrets.DINGTALK_WEBHOOK }}" || true
```

---

## 四、备选方案：阿里云云效 (Apsara DevOps) 国内极速流水线

如果你的团队代码托管在 Gitee 或阿里云 Codeup，或者不想走 GitHub，可以使用**阿里云云效**（对 30 人以下团队完全免费）：

1. 打开 [阿里云云效流水线 Flow](https://flow.aliyun.com/)；
2. 新建流水线 -> 选择模板「**Java/Python/Node 容器构建并部署到 ECS**」；
3. 配置流水线触发事件：代码分支为 `prd` 时自动触发；
4. 构建节点：
   - 任务 1：`Node.js 构建` -> 执行 `cd frontend && pnpm install && pnpm build`；
   - 任务 2：`镜像构建并推送至阿里云 ACR`；
   - 任务 3：`ECS 主机部署` -> 选择目标 ECS 实例，直接运行 `docker compose -f docker-compose.prod.yml up -d`；
5. 云效运行在阿里云内网，整个打包发布流程只需 **1 ~ 2 分钟**，速度极快！

---

## 五、学生团队开发实战演练：从发 PR 到全自动上线

在教学中，向学生演示标准的现代互联网企业开发流：

```bash
# 1. 学生在自己的功能分支上开发完毕并测试通过
git checkout -b feature/login-optimize
git add .
git commit -m "feat: 优化登录状态与DAG加载性能"
git push origin feature/login-optimize

# 2. 在 GitHub/Gitee 上发起 Pull Request (PR):
#    源分支: feature/login-optimize  --->  目标分支: prd

# 3. 教师/技术负责人 Review 代码无误后，点击 "Merge pull request"

# 4. 此时打开 GitHub 的 "Actions" 选项卡，可以看到绿色的齿轮正在飞速运转：
#    [✓] Checkout Code (2s)
#    [✓] Build and Push Backend (45s)
#    [✓] Build and Push Frontend (30s)
#    [✓] Deploy to ECS (15s)
#    [✓] Health check passed 200 OK!

# 5. 刷新生产网址 https://ai.yourdomain.com，新功能已经毫秒级呈现在线上！
```
这就是真正的工业级持续交付（CI/CD）的魅力！
