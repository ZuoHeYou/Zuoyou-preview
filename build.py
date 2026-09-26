"""仅将公开白名单数据和已核验图片构建为静态站点，不读取内部 Wiki。"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from render import STATES, render_pages

SOURCE = Path(__file__).resolve().parent


def load_data():
    progress = json.loads((SOURCE / "data/progress.json").read_text())
    media = json.loads((SOURCE / "data/media.json").read_text())
    modules = progress["modules"]
    ids = [module["id"] for module in modules]
    if len(ids) != len(set(ids)) or not all(re.fullmatch(r"MOD-\d{2}", i) for i in ids):
        raise ValueError("模块编号重复或格式无效")
    assets = [image["asset"] for image in media["images"]]
    if len(assets) != len(set(assets)):
        raise ValueError("图片附件名重复")
    for image in media["images"]:
        if not re.fullmatch(r"[a-z0-9-]+\.(png|webp|jpg)", image["asset"]):
            raise ValueError("图片文件名须为安全的相对文件名")
        if not re.fullmatch(r"[0-9a-f]{64}", image["sha256"]):
            raise ValueError("图片必须登记 SHA-256")
        if any(type(image[key]) is not int or image[key] <= 0 for key in ("width", "height")):
            raise ValueError("图片尺寸须为正整数")
    requirements = json.loads((SOURCE / "data/requirements.json").read_text())
    image_ids = [image["id"] for image in media["images"]]
    if len(image_ids) != len(set(image_ids)):
        raise ValueError("图片 ID 重复")
    all_ids = set(ids)
    used_media = set()
    represented = set()
    for group in requirements["groups"]:
        gid = group["id"]
        if not re.fullmatch(r"REQ-\d{2}-\d{2}", gid) or gid in all_ids:
            raise ValueError("二级功能编号无效或重复")
        parent = "MOD-" + gid[4:6]
        if parent not in ids or not group["items"]:
            raise ValueError("二级功能缺少有效模块或三级验收点")
        represented.add(parent)
        all_ids.add(gid)
        for item in group["items"]:
            iid = item["id"]
            if not re.fullmatch("AC-" + gid[4:] + r"-\d{2}", iid) or iid in all_ids:
                raise ValueError("三级验收点编号重复或与父级不一致")
            all_ids.add(iid)
            if item["status"] not in STATES:
                raise ValueError("未知三级状态")
            if item["status"] in {"todo", "unknown", "skeleton"} and item["previews"]:
                raise ValueError("未实现或仅骨架的验收点不能关联实现截图")
            for ref in item["previews"]:
                if ref["id"] not in image_ids or not ref["note"].strip():
                    raise ValueError("图片关联不存在或缺少展示边界说明")
                used_media.add(ref["id"])
    if represented != set(ids):
        raise ValueError("存在未拆分模块")
    if used_media != set(image_ids):
        raise ValueError("图片白名单包含未关联图片，请移出发布清单")
    return progress, requirements, media


def materialize_images(media, media_dir, output, repository):
    media_dir.mkdir(parents=True, exist_ok=True)
    for image in media["images"]:
        source = media_dir / image["asset"]
        if not source.exists():
            if not repository:
                raise ValueError(f"缺少图片 {image['asset']}；提供 --repository 从 Release 下载")
            subprocess.run([
                "gh", "release", "download", media["release"], "--repo", repository,
                "--pattern", image["asset"], "--dir", str(media_dir),
            ], check=True)
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != image["sha256"]:
            raise ValueError(f"图片校验失败：{image['asset']}，停止发布")
        shutil.copyfile(source, output / "media" / image["asset"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(SOURCE.parent / "build/pages"))
    parser.add_argument("--media-dir", default=str(SOURCE.parent / "build/preview-media"))
    parser.add_argument("--repository", help="仅从指定 GitHub 仓库的 Release 下载图片")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    # 每次使用空目录，避免上次构建遗留的文件意外对外发布。
    if output.exists() and any(output.iterdir()):
        raise ValueError("输出目录必须为空，请为本次构建指定新的临时目录")
    progress, requirements, media = load_data()
    (output / "media").mkdir(parents=True, exist_ok=True)
    materialize_images(media, Path(args.media_dir), output, args.repository)
    pages = render_pages(progress, requirements, media)
    for filename, content in pages.items():
        (output / filename).write_text(content)
    for filename in ("site.css", "reader.css", "site.js"):
        shutil.copyfile(SOURCE / filename, output / filename)
    (output / ".nojekyll").touch()
    expected = set(pages) | {"site.css", "reader.css", "site.js", ".nojekyll"} | {
        "media/" + i["asset"] for i in media["images"]
    }
    actual = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("构建产物超出发布白名单")
    print(f"已生成 {len(progress['modules'])} 个模块、{len(pages)} 个分层页面、{len(media['images'])} 张演示图：{output}")


if __name__ == "__main__":
    main()
