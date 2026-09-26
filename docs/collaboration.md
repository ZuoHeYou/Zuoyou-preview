# 双人图片协作与发布

两人直接在本仓库 master 协作。只发布经过筛选的进度摘要和演示图，不加入 PRD 原文、内部 Wiki、业务源码或真实用户数据。

## 图片合并规则

1. 开工先约定负责的 REQ／AC；在干净工作区拉取最新 master。两人处理不同需求时各自追加图片条目，同一验收点的状态、证据或图片变更需要核对后合并。
2. 图片在 Git 外保存，人工审阅后使用“功能名-日期-SHA256前12位.png”命名，索引保存完整 SHA-256、尺寸、设备和日期。新截图用新文件名，不能替换旧文件内容。
3. 统一向 `ZuoHeYou/Zuoyou-preview` 的 `preview-media-20260926` Release 追加附件。当前索引只有一个全局 `release` 字段，不按个人或每次发布新建 Release，也不随意改该字段，否则旧图会找不到。
4. 先上传附件，再更新 `data/media.json` 和 `data/requirements.json` 中对应 AC 的 `previews` 引用。图片 ID 唯一；替换某个 ID 的版本会影响全部引用它的验收点，应逐项检查。仅用于某个新场景时新增 ID。
5. 合并的是 JSON 文本和引用关系，不合并图片二进制。相同 AC 出现冲突时共同核对语义、状态和展示范围；不能直接用某一方整份文件覆盖另一方。
6. 新图片不会自动出现在站点，须合并索引并成功部署。已上传但尚未引用的附件不会进入构建；不要删除仍被历史索引引用的附件。清理旧附件应另行评估历史构建和回退需求。

上传示例（将示例路径换成实际文件，已登录 GitHub CLI 的账号需要仓库写权限）：

```sh
gh release upload preview-media-20260926 /实际路径/功能名-日期-hash.png --repo ZuoHeYou/Zuoyou-preview
```

不使用 `--clobber`。同名附件已存在时，核对完整 hash；一致则复用，不一致则使用新的正确 hash 文件名。上传成功后使用空图片缓存构建，可检查另一位开发者和 CI 能否下载。

## 发布顺序

在本仓库干净工作区执行 `git pull --ff-only origin master` 后开发，提交前运行：

```sh
python3 -m unittest discover -s tests -v
python3 build.py --repository ZuoHeYou/Zuoyou-preview
```

默认输出为本仓库 `build/pages/`，必须为空；重复验证可用 `--output` 指定新的空目录。若要验证远程附件，用 `--media-dir` 指定新的空缓存。

使用中文 Conventional Commits 提交本仓库改动。推送前 fetch，如远程有新提交，只 rebase 尚未推送的本地提交；冲突处理后重新验证。推送 `master`，检查 Actions 测试、图片校验及 Pages 部署成功，不强推。Pages 展示本仓库最新成功部署的 master，业务仓库的子模块指针用于记录关联版本，并不直接控制线上版本。

作为业务仓库子模块时，必须先推送本仓库，再提交业务仓库的 `preview` 版本指针与关联文档并推送。不要让父仓库引用仅存在本机的提交。两人同时更新指针时，先在预览 master 集成双方提交，再将父仓库指针更新至包含双方工作的版本；不盲选 ours／theirs。

## 另一位开发者同步

首次克隆业务仓库使用 `git clone --recurse-submodules <业务仓库地址>`。已有业务仓库时，先确认子模块无未提交改动，再运行：

```sh
git submodule update --init --recursive
```

该命令检出父仓库记录的版本，通常是 detached HEAD。需要修改预览时，在干净状态下切回分支：

```sh
git -C preview switch master
git -C preview pull --ff-only origin master
```

单独使用本公开仓库时直接克隆即可。业务仓库更新后，再运行子模块初始化／更新命令同步记录的版本；不要用 `--force` 覆盖本地工作。
