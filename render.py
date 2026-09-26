"""渐进展示：模块 → 功能 → 验收点 → 已关联预览。"""

import html
import re
from pathlib import Path
from reader import bind_book

SOURCE = Path(__file__).resolve().parent
STATES = {
    "implemented": "已实现", "partial": "部分实现", "demo": "本地演示",
    "skeleton": "仅有框架", "todo": "未实现", "unknown": "待核验",
}


def escape(value):
    return html.escape(str(value), quote=True)


def url(identifier):
    return identifier.lower() + ".html"


def aggregate(items):
    states = {item["status"] for item in items}
    if len(states) == 1:
        return next(iter(states))
    if states & {"implemented", "demo", "partial"}:
        return "partial"
    return "skeleton" if "skeleton" in states else "unknown"


def badge(state):
    return f'<span class="badge {state}">{STATES[state]}</span>'


def state_summary(items):
    return " · ".join(
        f'{label} {sum(i["status"] == state for i in items)}'
        for state, label in STATES.items() if any(i["status"] == state for i in items)
    )


def link(identifier, label):
    return f'<a href="{url(identifier)}">{escape(label)}</a>'


def shell(title, content, crumbs=()):
    trail = '<a href="index.html">模块总览</a>'
    for identifier, name in crumbs:
        trail += '<span aria-hidden="true">/</span>'
        trail += link(identifier, name) if identifier else f'<span aria-current="page">{escape(name)}</span>'
    replacements = {"TITLE": escape(title), "CONTENT": content,
                    "BREADCRUMBS": f'<nav class="breadcrumbs" aria-label="面包屑">{trail}</nav>' if crumbs else ""}
    return re.sub(r"\{\{([A-Z]+)\}\}", lambda m: replacements[m[1]],
                  (SOURCE / "templates/index.html").read_text())


def heading(level, identifier, name, description, state=None):
    return (f'<section class="detail-heading"><p class="eyebrow">{escape(level)} · {escape(identifier)}</p>'
            f'<h1 id="page-title">{escape(name)}</h1><p class="intro">{escape(description)}</p>'
            f'{badge(state) if state else ""}</section>')


def render_overview(progress, groups):
    cards = []
    for module in progress["modules"]:
        children = [g for g in groups if g["id"][4:6] == module["id"][4:6]]
        items = [item for g in children for item in g["items"]]
        state = aggregate(items)
        search = " ".join([g["title"] for g in children] + [i["title"] for i in items])
        cards.append(
            f'<article class="module-card" data-status="{state}" data-search="{escape(search)}">'
            f'<div class="card-top"><span class="module-id">{module["id"]}</span>{badge(state)}</div>'
            f'<h3>{link(module["id"], module["name"])}</h3>'
            f'<p class="children-summary">{escape(" / ".join(g["title"] for g in children))}</p>'
            f'<p class="item-count">{len(children)} 个二级功能 · {len(items)} 个三级验收点</p>'
            f'<a class="text-link" href="{url(module["id"])}">查看功能拆分 <span aria-hidden="true">→</span></a></article>'
        )
    counts = [("一级模块", len(progress["modules"])), ("二级功能", len(groups)),
              ("三级验收点", sum(len(g["items"]) for g in groups))]
    metrics = "".join(f'<div class="metric"><strong>{n}</strong><span>{name}</span></div>' for name, n in counts)
    options = "".join(f'<option value="{key}">{name}</option>' for key, name in STATES.items())
    verification = "".join(
        f'<article class="verification-card"><strong>{escape(v["value"])}</strong>'
        f'<h3>{escape(v["label"])}</h3><p>{escape(v["detail"])}</p></article>' for v in progress["verification"])
    content = (
        '<section class="hero"><p class="eyebrow"><span class="dot"></span> 左右 · 需求进度</p>'
        f'<h1 id="page-title">从模块到功能，<br>逐项查看<span>完成情况。</span></h1><p class="intro">{escape(progress["intro"])}</p>'
        f'<div class="hero-meta"><span>{escape(progress["basis"])}</span><span>更新 {escape(progress["updated"])}</span></div></section>'
        f'<section class="overview hierarchy-counts" aria-label="需求层级统计">{metrics}</section>'
        f'<p class="scope">{escape(progress["scope"])}</p>'
        '<section id="modules"><div class="section-heading"><div><p class="eyebrow">一级 / MODULES</p>'
        '<h2>选择一个模块</h2></div><p>二级功能 → 三级验收点 → 对应预览</p></div>'
        '<div class="filters" hidden><label class="search">搜索需求 <input id="search" type="search" '
        'placeholder="模块、功能或具体行为" autocomplete="off"></label><label>模块阶段 '
        f'<select id="status"><option value="all">全部阶段</option>{options}</select></label>'
        '<span id="result-count" role="status" aria-live="polite"></span></div>'
        '<p class="scope">模块阶段由下级验收点汇总；点击进入后可查看各项差异。搜索也匹配下级功能。</p>'
        f'<div class="module-grid">{"".join(cards)}</div><p id="empty" class="empty" hidden>没有匹配的模块，试试其他关键词。</p></section>'
        '<section id="verification"><div class="section-heading"><div><p class="eyebrow">验证摘要</p><h2>已验证的范围</h2></div>'
        f'<p>记录日期：{escape(progress["updated"])}</p></div><div class="verification-grid">{verification}</div>'
        '<p class="scope">记录口径不同，不相加为业务验收点；预览图在具体需求中查看，不作为功能完成的唯一证据。</p></section>'
    )
    return shell("产品需求进度", content)


def render_module(module, groups):
    items = [item for g in groups for item in g["items"]]
    content = heading("一级模块", module["id"], module["name"], "选择二级功能，继续查看具体验收点。", aggregate(items))
    content += f'<p class="scope">{escape(state_summary(items))}。汇总按三级项统计，不表示交付比例。</p><div class="requirements-list">'
    for group in groups:
        content += (
            f'<article class="requirement-row"><div><p class="module-id">{group["id"]} · 二级功能</p>'
            f'<h2>{link(group["id"], group["title"])}</h2><p>{escape(group["source"])}</p>'
            f'<p>{len(group["items"])} 个三级验收点 · {escape(state_summary(group["items"]))}</p></div>'
            f'<div class="row-action">{badge(aggregate(group["items"]))}'
            f'<a class="text-link" href="{url(group["id"])}">查看验收点 →</a></div></article>'
        )
    return shell(module["name"], content + "</div>", [(None, module["name"])])


def render_group(module, group):
    content = heading("二级功能", group["id"], group["title"], "按三级验收点查看实现状态和对应预览。", aggregate(group["items"]))
    content += f'<p class="scope">来源：{escape(group["source"])} · {escape(group["kind"])}。项目拆分编号，不是 PRD 原文编号。</p>'
    content += '<div class="requirements-list">'
    for item in group["items"]:
        images = f'{len(item["previews"])} 张相关预览' if item["previews"] else '暂无对应预览图'
        content += (
            f'<article class="requirement-row"><div><p class="module-id">{item["id"]} · 三级验收点</p>'
            f'<h2>{link(item["id"], item["title"])}</h2><p>{escape(item["criterion"])}</p>'
            f'<p class="preview-count">{images}</p></div><div class="row-action">{badge(item["status"])}'
            f'<a class="text-link" href="{url(item["id"])}">查看详情与预览 →</a></div></article>'
        )
    return shell(group["title"], content + "</div>", [(module["id"], module["name"]), (None, group["title"])])


def render_item(module, group, item, images, date):
    content = heading("三级验收点", item["id"], item["title"], item["criterion"], item["status"])
    content += (f'<section class="evidence"><h2>当前实现与验证</h2><p>{escape(item["note"])}</p>'
                f'<p class="scope">来源：{escape(group["source"])} · {escape(group["kind"])} · 更新 {escape(date)}</p></section>'
                '<section id="previews"><div class="section-heading"><h2>对应预览</h2></div>')
    if not item["previews"]:
        content += '<div class="empty-preview"><strong>暂无对应预览图</strong><p>当前条目未关联截图。已有实现或测试记录见上方，后续补充该行为对应的画面。</p></div>'
    else:
        content += '<div class="detail-gallery">'
        for reference in item["previews"]:
            image = images[reference["id"]]
            src = "media/" + image["asset"]
            content += (
                f'<figure class="preview-card"><a href="{src}" target="_blank" rel="noopener" '
                f'aria-label="查看{escape(image["title"])}原图（新窗口）"><img src="{src}" '
                f'alt="{escape(image["title"])}演示截图" width="{image["width"]}" height="{image["height"]}" loading="lazy"></a>'
                f'<figcaption><span class="badge demo">本地演示</span><h3>{escape(image["title"])}</h3>'
                f'<p>{escape(reference["note"])}</p><p>{escape(image["device"])}</p>'
                f'<time>{escape(image["date"])}</time><p class="scope">点击图片查看原尺寸。</p></figcaption></figure>'
            )
        content += '</div><p class="scope">截图只证明可见画面，不替代交互、接口或业务验收；图中数据为演示数据。</p>'
    crumbs = [(module["id"], module["name"]), (group["id"], group["title"]), (None, item["title"])]
    return shell(item["title"], content + "</section>", crumbs)


def render_pages(progress, requirements, media):
    groups = requirements["groups"]
    images = {image["id"]: image for image in media["images"]}
    pages = {"index.html": render_overview(progress, groups)}
    for module in progress["modules"]:
        children = [g for g in groups if g["id"][4:6] == module["id"][4:6]]
        pages[url(module["id"])] = render_module(module, children)
        for group in children:
            pages[url(group["id"])] = render_group(module, group)
            for item in group["items"]:
                pages[url(item["id"])] = render_item(module, group, item, images, progress["updated"])
    return bind_book(pages, progress, requirements)
