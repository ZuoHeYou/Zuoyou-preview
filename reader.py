"""为静态需求页增加书籍目录、页码与前后页导航。"""

from html import escape


def filename(identifier):
    return identifier.lower() + ".html"


def entry(path, title, current, level=""):
    selected = ' aria-current="page"' if path == current else ""
    return (f'<a class="toc-link {level}" href="{path}"{selected}>'
            f'{escape(title)}</a>')


def directory(progress, requirements, current):
    parts = ['<aside id="reader-directory" class="reader-directory" aria-label="需求手册目录">'
             '<div class="directory-heading"><span>CONTENTS</span><h2>需求目录</h2>'
             '<p>展开章节，直接跳到具体需求。</p></div><nav aria-label="章节目录">',
             entry("index.html", "扉页 · 项目总览", current)]
    for module in progress["modules"]:
        groups = [g for g in requirements["groups"] if g["id"][4:6] == module["id"][4:6]]
        paths = [filename(module["id"])]
        for group in groups:
            paths += [filename(group["id"])] + [filename(i["id"]) for i in group["items"]]
        opened = " open" if current in paths else ""
        parts.append(f'<details class="toc-module"{opened}><summary><span>{module["id"][4:]}</span>'
                     f'{escape(module["name"])}</summary>{entry(filename(module["id"]), "章节概览", current)}')
        for group in groups:
            paths = [filename(group["id"])] + [filename(i["id"]) for i in group["items"]]
            opened = " open" if current in paths else ""
            parts.append(f'<details class="toc-group"{opened}><summary>{escape(group["title"])}</summary>'
                         f'{entry(filename(group["id"]), "功能概览", current)}')
            for item in group["items"]:
                parts.append(entry(filename(item["id"]), item["title"], current, "toc-item"))
            parts.append("</details>")
        parts.append("</details>")
    return "".join(parts) + "</nav></aside>"


def bind_book(pages, progress, requirements):
    order = list(pages)
    titles = {"index.html": "项目总览"}
    titles.update({filename(m["id"]): m["name"] for m in progress["modules"]})
    for group in requirements["groups"]:
        titles[filename(group["id"])] = group["title"]
        titles.update({filename(i["id"]): i["title"] for i in group["items"]})
    result = {}
    for index, path in enumerate(order):
        links = []
        for direction, offset, label, symbol in (("previous", -1, "上一页", "←"), ("next", 1, "下一页", "→")):
            target = index + offset
            if 0 <= target < len(order):
                destination = order[target]
                links.append(f'<a class="page-control {direction}" data-turn="{direction}" href="{destination}">'
                             f'<span>{symbol} {label}</span><strong>{escape(titles[destination])}</strong></a>')
            else:
                links.append(f'<span class="page-control {direction} disabled" aria-disabled="true">'
                             f'<span>{"已到扉页" if offset < 0 else "已到末页"}</span></span>')
        pagination = (f'<nav class="page-turner" aria-label="翻页">{links[0]}'
                      f'<span class="page-number">{index + 1} <span>/ {len(order)}</span></span>{links[1]}</nav>')
        page = pages[path].replace('<main id="main">',
            '<div class="book-layout">' + directory(progress, requirements, path) +
            f'<main id="main" class="reader-sheet" data-page="{path}" tabindex="-1">'
            '<div class="running-head"><span>左右 · 产品需求手册</span>'
            f'<span>{index + 1:03} / {len(order):03}</span></div>')
        page = page.replace('</main>', pagination + '</main></div>')
        result[path] = page
    return result
