# 部署界限

## 本地演示

```sh
./software/start.sh
```

无需依赖安装、数据库服务、模型 API、网络连接。仅 `127.0.0.1:8765`。服务端允许 Host 为实际端口的 127.0.0.1 / localhost，校验 Origin，拒绝 cross-site，设置 no-store、CSP、自身脚本、nosniff、no-referrer 和 frame-ancestors none。静态文件只有固定四项白名单，无法读数据库、源码、.env 或任意目录。单请求体 32 KiB、连接读取 5 秒超时、字段长度/枚举/范围限制，不支持 Transfer-Encoding。数据目录文件通过进程 umask 077 创建。

`/health` 和公开 Agent Card 不需令牌；业务接口全部需 Bearer。没有通过页面选择角色的公开令牌签发入口。启动时只初始化合成身份和合成授权，终端打印两类访问链接。此模式不支持导入真实企业数据、员工注册或 SSO。

## Docker

```sh
docker build -t lingban-local:0.1 software
docker run --rm --name lingban-local \
  -p 127.0.0.1:8765:8765 \
  -v lingban-demo-data:/app/software/data lingban-local:0.1
```

容器内以 UID/GID 10001 运行并显式监听 0.0.0.0，宿主机端口映射仍必须绑定 127.0.0.1。默认裸机启动保持回环；非回环要同时显式指定 `--host 0.0.0.0 --allow-network`。不要把示例改成公开 `-p 8765:8765`。数据库 volume 重启保留授权与任务，令牌在每次启动轮换。

当前本机 Docker CLI 存在，但 daemon 未运行；未启动/修改系统 Docker 服务，未实际 build/run。Dockerfile 为待验证交付，不声称容器验收已通过。

## 真实部署前仍需

此 Python http.server 原型不是公网生产服务：没有 TLS/SSO、令牌到期/细粒度撤销后台、请求速率限制、存储配额、分页 UI、跨进程 worker 调度、完整监控或加密备份。单进程 RLock + SQLite 适用于本地演示。数据库含个人合成任务，不应拷贝为真实员工数据存储方案。

真实部署需正式 Web 服务器、TLS、身份与组织生命周期、审计保存策略、数据保留/删除与备份设计、聚合抗差分方案、安全测试，以及所有同意界面的法务/隐私复核。指标 >=5 不等于完整匿名化。无秘密采集、无自动员工评分或雇佣决策。不能用本原型证明硬件量产、认证、医学性能或 MCP/A2A 认证互通。

没有模型适配器；未探查任何模型凭据。`LINGBAN_TOKEN` 只在用户显式启动 MCP/串口桥时读取，用于本地服务身份，不是模型 API Key。
