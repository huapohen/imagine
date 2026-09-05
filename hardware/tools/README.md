# 任务局部工具环境

已安装/使用 CadQuery 2.8.0（OpenCascade7.9.3）、trimesh5.1.0、Blender4.5.3、KiCad9.0.7；系统现有ffmpeg。Python venv、下载缓存和只读DMG挂载点全部位于hardware/tools或hardware/downloads。未执行brew全局安装，未接受KiCad全局库配置。GUI不是复现依赖。

当前命令：

```sh
hardware/tools/venv/bin/python hardware/cad/build_cad.py
hardware/tools/mount-blender/Blender.app/Contents/MacOS/Blender --version
hardware/tools/mount-kicad/KiCad/KiCad.app/Contents/MacOS/kicad-cli version
```

重启后重新挂载已验证的DMG：

```sh
mkdir -p hardware/tools/mount-blender hardware/tools/mount-kicad
hdiutil attach -readonly -nobrowse -mountpoint "$PWD/hardware/tools/mount-blender" hardware/downloads/blender.dmg
hdiutil attach -readonly -nobrowse -mountpoint "$PWD/hardware/tools/mount-kicad" hardware/downloads/kicad.dmg
```

重建venv先遵守AGENTS网络短测，采用已测可用的PyPI/可信镜像，再运行 `uv venv hardware/tools/venv --python 3.13` 与 `uv pip sync --python hardware/tools/venv/bin/python --require-hashes hardware/tools/requirements.lock`。Python3.13须已经存在；不要为便捷改系统Python。uv缓存使用`UV_CACHE_DIR="$PWD/hardware/tools/uv-cache"`。

网络证据：validation/network-probes.json、mirror-probes.json、download-progress.log。Blender经官方SHA256比对；KiCad DMG通过hdiutil内部校验且应用通过codesign严格验证，签发主体KiCad Services Corporation (9FQDHNY6U2)。首次Blender分段文件损坏已精确删除并重新完整下载，重新校验通过；未清空系统缓存。官方校验文本在downloads/blender.sha256。

主控集成时只打包源码/产物/文档，**不要把downloads、venv、uv-cache或mount-*应用树加入Git或发布包**。本会话不执行Git操作。
