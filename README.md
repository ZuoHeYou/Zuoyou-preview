# 左右公开进度页

本目录只包含允许公开的模块进度摘要、页面源码与演示图片索引。不包含 PRD 原文、设计源文件、内部讨论、业务代码或认证信息。

- `data/progress.json`：一级模块目录与验证摘要，不宣称整体完成百分比。
- `data/requirements.json`：项目自行拆分的二级功能与三级验收点；每项记录来源、状态、验证边界和图片关联。上层状态按三级项汇总。
- `data/media.json`：选定演示截图的 Release 附件名、SHA-256、日期和尺寸。图片二进制不进入此目录或 Git 历史。
- `build.py`：Python 3 标准库构建；缺图时可通过已登录的 GitHub CLI 下载 Release 附件。
- `render.py`：生成模块总览、模块详情、二级功能列表与三级验收详情。只有具体三级详情展示相关图片，无图时明确显示暂无预览。
- `reader.py` / `reader.css`：为页面加入常驻目录、纸张布局、页码和前后页链接；桌面目录可直接跳到三级需求，窄屏通过“打开目录”查看。脚本增强连续翻页、方向键与浏览器前进后退，减少动态效果时关闭翻页动画。
- `publishing/pages.yml`：独立展示仓库使用的工作流模板，部署时放置为 `.github/workflows/pages.yml`。

本地构建：`python3 preview/build.py --repository ZuoHeYou/Zuoyou-preview`。在独立展示仓库根目录执行时改为 `python3 build.py --repository ZuoHeYou/Zuoyou-preview`。

默认输出在此目录父级的 `build/pages/`，图片缓存为 `build/preview-media/`；构建目录必须为空，也可以通过 `--output` 指定新的临时目录。预览用 `python3 -m http.server 8765 --bind 127.0.0.1 --directory build/pages`。

发布只同步明确列出的源码文件及三份 JSON，构建产物通过 Actions artifact 发布到 Pages，不提交产物分支。新增图片须先检查可公开内容、上传版本化 Release 附件，再更新索引并关联到具体验收点；原图 hash 不匹配、父子编号不一致或引用未知图片时停止构建。公开附件与页面同样可被任何人下载。

公开页是截至标注日期的进度快照。未经真实业务联调与验收，不把本地演示、页面壳或部分平台测试标为业务已完成。
