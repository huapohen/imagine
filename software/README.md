# 灵伴 LINGBAN · 本地主动 Agent 原型

全部为合成演示数据。电脑运行确定性规则 Agent，透明晶鼠为原创概念插画和交互模拟。默认离线；可显式启用受限的第三方模型合成测试。无外部消息发送、录音摄像、生理推断或员工评分。名称与商标待检索。

## 一键启动

```sh
./software/start.sh
```

Python 3.9+，仅标准库，无需 pip。默认 `http://127.0.0.1:8765`，数据库在 `software/data/lingban.sqlite3`。终端显示员工和企业两个带片段令牌的链接；打开后令牌从地址栏清除，仅在页面内存持有。重启会轮换令牌，不恢复撤销的授权。链接持有者拥有对应角色权限，请勿分享。

```sh
./software/start.sh --port 8766 --db data/custom.sqlite3
```

注意脚本工作目录为 software，因此自定义数据库建议使用绝对路径或 `--db data/custom.sqlite3`。板级与可选模型集成当前共通过 59 项离线回归测试；完整接口、测试及限制见 `COMPLETION.md` 和 `../docs/software/README.md`。

## 快速体验

1. 员工工作台点击「会议将近」或「项目阻塞」，查看提醒及判断依据。
2. 点击「专注与休息」：新提醒暂缓；点击「结束专注」查看休息建议。
3. 批准待办动作，只生成本地 outbox；拒绝无 outbox。
4. 另开企业令牌链接，初始可见 5 位合成员工的聚合。员工撤销分享，企业立即隐藏结果。

服务端根据 Bearer 令牌识别角色和归属。页面没有权限切换后门。插件只做 manifest 注册和受限 API 调用，不加载第三方代码。串口模拟与固件见 `../firmware/README.md`。

## 复现测试

本轮板级/LB1固定回归从仓库根目录执行 `./software/test-integration.sh`，不包含并行模型测试。全量集成测试由主控执行：

```sh
cd software
python3 -m unittest discover -s tests -v
```

## 临时真实模型测试

仅本机明确启用：`./software/start.sh --local-model-test`（从仓库根目录执行）。配置只从权限为 0600、Git 忽略的根 `.env` 读取，容器镜像不包含该文件。员工在行动审批区同意本次固定合成场景后生成草稿，仍须批准才保存本地 outbox。默认启动不调用模型。完整预算、复现与实测见 [MODEL_INTEGRATION.md](../docs/software/MODEL_INTEGRATION.md)。
