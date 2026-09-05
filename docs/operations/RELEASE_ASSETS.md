# 私有Release附件

版本：[`v0.1.0-evt-a-20260906`](https://github.com/huapohen/imagine/releases/tag/v0.1.0-evt-a-20260906)。仓库保持私有，需要已授权GitHub账号访问。

视频和评审ZIP在本机已经生成；它们作为Release附件分发，避免普通Git历史反复存储大媒体。源码、PPTX/PDF、文档、渲染图和验证报告在仓库内。

|附件|用途/恢复位置|
|---|---|
|`01_crystal_mouse_focus.mp4` 至 `08_robot_extension.mp4`|八条2K/15秒成片，放入`media/final/`|
|`LINGBAN_8_concepts_2min.mp4`|2K/120秒合集，放入`media/final/`|
|`lingban-software-demo.mp4`|28秒真实浏览器软件演示，放入`media/demo/`|
|`lingban_evt_a_review.zip`|完整硬件数字工程评审包，NOT-FOR-FAB|
|`lingban_factory_review.zip`|硬件、固件源/接口、RFQ与验收整合包；先读包内`FACTORY_START_HERE.md`|
|`lingban_minimax_originals.zip`|8条未修改的提供方原片，保留AIGC元数据；解压到仓库根即还原`media/generated/`|
|`SHA256SUMS.txt`|上述13个文件的精确SHA-256；同内容机读清单见[RELEASE_ASSETS.json](RELEASE_ASSETS.json)|

## 新电脑恢复

在仓库根目录、已登录具有仓库权限的`gh`环境执行：

```sh
gh release download v0.1.0-evt-a-20260906 --repo huapohen/imagine --pattern '0*.mp4' --pattern 'LINGBAN*.mp4' --dir media/final
gh release download v0.1.0-evt-a-20260906 --repo huapohen/imagine --pattern 'lingban-software-demo.mp4' --dir media/demo
gh release download v0.1.0-evt-a-20260906 --repo huapohen/imagine --pattern 'lingban_*_review.zip' --dir hardware/delivery
gh release download v0.1.0-evt-a-20260906 --repo huapohen/imagine --pattern 'lingban_minimax_originals.zip' --pattern 'SHA256SUMS.txt' --dir release
```

下载后对照机读清单的`local_path`和`sha256`核验；同名文件已存在时`gh`默认拒绝覆盖。原片ZIP只在需要重新后期时下载，不是播放成片的前置条件。

本地重算附件哈希：`python3 scripts/release_manifest.py`。模型`.env`、API账本/限时下载地址、角色令牌、软件数据库、CLI私有日志、安装包和工具环境均不进入附件。
