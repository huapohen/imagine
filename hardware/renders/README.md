# 概念渲染与转台

本地Blender/Cycles渲染，源网格来自同批CAD导出的STL。不是硬件照片，未打样/认证。光环、发光窗和屏幕内容为视觉示意/合成数据；不代表当前低电流LED已经达到光环均匀效果。

```sh
hardware/tools/mount-blender/Blender.app/Contents/MacOS/Blender -b -t 8 --python hardware/renders/render_scene.py -- hero
hardware/tools/mount-blender/Blender.app/Contents/MacOS/Blender -b -t 8 --python hardware/renders/render_scene.py -- exploded
hardware/tools/mount-blender/Blender.app/Contents/MacOS/Blender -b -t 8 --python hardware/renders/render_scene.py -- turntable
hardware/tools/venv/bin/python hardware/renders/finish_media.py
```

`lingban_hero.blend`内已保存120帧/24fps、线性完整旋转的关键帧源；`render_scene.py`可确定性重建灯光、材质、相机、爆炸间距与转台。演示MP4使用每4帧抽样、6fps回放，约5秒一周；不是实时交互。PNG附有概念标识，可直接交pitch；raw文件只供后处理，外发须使用带标识版本。
