#!/usr/bin/env python3
"""Render a limited Markdown subset into an offline, mobile-friendly WeChat article preview.
No external dependencies, no network or publication actions. Untrusted HTML is escaped.
"""
from __future__ import annotations

import argparse
import base64
import html
import pathlib
import re
import sys

ARTICLE_COLOR = "#273449"
ACCENT = "#265bc0"


def inline(text: str) -> str:
    """Render only safe inline Markdown; escape HTML first."""
    escaped = html.escape(text, quote=True)
    escaped = re.sub(
        r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)",
        lambda m: '<a href="' + m.group(2) + '" target="_blank" rel="noopener noreferrer" '
        'style="color:#265bc0;text-decoration:underline">' + m.group(1) + '</a>',
        escaped,
    )
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        lambda m: '<strong style="font-weight:700;color:#164589">' + m.group(1) + '</strong>',
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", lambda m: '<code style="background:#f0f4fa;padding:2px 4px;border-radius:4px">' + m.group(1) + '</code>', escaped)
    return escaped


def parse_markdown(markdown: str) -> tuple[str, str]:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    title = "公众号文章预览"
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_kind = None

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(x.strip() for x in paragraph)
            blocks.append(f'<p style="font-size:16px;line-height:1.95;color:{ARTICLE_COLOR};margin:0 0 22px;letter-spacing:.015em;word-wrap:break-word">{inline(text)}</p>')
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_items:
            tag = "ol" if list_kind == "ol" else "ul"
            blocks.append(f'<{tag} style="font-size:16px;line-height:1.9;padding-left:24px;margin:0 0 24px;color:{ARTICLE_COLOR}">' + "".join(list_items) + f'</{tag}>')
            list_items.clear()
            list_kind = None

    found_h1 = False
    for raw in lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        if line.startswith("# ") and not found_h1:
            flush_paragraph()
            flush_list()
            title = line[2:].strip()
            found_h1 = True
            continue
        match_heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if match_heading:
            flush_paragraph()
            flush_list()
            level = len(match_heading.group(1))
            heading = match_heading.group(2)
            if level == 1:
                blocks.append(f'<h2 style="font-size:19px;font-weight:700;line-height:1.5;color:#153b78;margin:34px 0 16px">{inline(heading)}</h2>')
            elif level == 2:
                blocks.append(f'<h2 style="font-size:19px;font-weight:700;line-height:1.5;color:#153b78;margin:34px 0 16px">{inline(heading)}</h2>')
            else:
                blocks.append(f'<h3 style="font-size:17px;font-weight:700;line-height:1.5;color:#153b78;margin:28px 0 14px">{inline(heading)}</h3>')
            continue
        match_bullet = re.match(r"^([-*]|\d+\.)\s+(.+)$", line)
        if match_bullet:
            flush_paragraph()
            kind = "ol" if match_bullet.group(1).endswith(".") else "ul"
            if list_items and list_kind != kind:
                flush_list()
            list_kind = kind
            list_items.append(f'<li style="margin:0 0 8px">{inline(match_bullet.group(2))}</li>')
            continue
        if line.startswith("> "):
            flush_paragraph()
            flush_list()
            blocks.append('<blockquote style="margin:12px 0 24px;padding:13px 18px;border-left:3px solid #285fc1;background:#f4f7fd;color:#4e5d74;line-height:1.8;font-size:15px">' + inline(line[2:]) + '</blockquote>')
            continue
        flush_list()
        paragraph.append(line)
    flush_paragraph()
    flush_list()
    return title, "\n".join(blocks)


STYLE = """
.cover-preview { display:block; width:100%; height:auto; border-radius:12px; margin:0 0 28px; }
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif; background:#eef2f8; color:#23344f; }
.toolbar { position:sticky; top:0; z-index:2; background:rgba(255,255,255,.92); backdrop-filter:blur(16px); border-bottom:1px solid #dae3ef; }
.toolbar-inner { max-width:900px; margin:auto; display:flex; align-items:center; gap:12px; padding:14px 20px; }
.brand { margin-right:auto; font-size:13px; font-weight:700; color:#2c4c83; letter-spacing:.04em; }
button { border:1px solid #ccd9ed; background:#fff; border-radius:10px; padding:10px 14px; color:#28466d; font-size:13px; cursor:pointer; font-weight:600; }
button.primary { background:#265bc0; color:white; border-color:#265bc0; }
button:hover { filter:brightness(.96); }
.wrap { max-width:850px; margin:36px auto 60px; padding:0 18px; }
.paper { background:#fff; border:1px solid #e0e7f1; border-radius:18px; box-shadow:0 20px 64px rgba(34,60,100,.08); overflow:hidden; }
.hero { padding:46px 58px 32px; border-bottom:1px solid #e9eef6; }
.eyebrow { font-size:11px; letter-spacing:.16em; color:#7487a3; text-transform:uppercase; font-weight:700; }
h1 { font-size:32px; line-height:1.45; letter-spacing:-.02em; margin:14px 0 20px; font-weight:800; color:#152b4e; }
.hero-meta { display:flex; gap:18px; color:#8190a6; font-size:12px; flex-wrap:wrap; }
.content { padding:40px 58px 44px; }
.note { margin:18px 8px 0; color:#75849b; font-size:12px; text-align:center; line-height:1.7; }
.status { min-height:20px; color:#265bc0; font-size:12px; padding-left:4px; }
@media (max-width:680px) {
 body {background:#fff;} .toolbar-inner {gap:8px; flex-wrap:wrap; padding:10px 12px;} .brand {width:100%; margin-bottom:2px;} button {flex:1;padding:9px 8px;}
 .wrap {margin:0 auto; padding:0;} .paper {border:none;border-radius:0;box-shadow:none;}
 .hero {padding:36px 23px 24px;} h1 {font-size:25px;} .content {padding:29px 23px 55px;} .note {padding:0 15px 20px;}
}
@media print { .toolbar,.note { display:none !important; } body {background:#fff;} .wrap {margin:0;padding:0;max-width:none;} .paper {box-shadow:none;border:none;} .hero,.content {padding-left:28px;padding-right:28px;} }
"""

JS = r"""
function showStatus(message) {
 const el = document.getElementById('copy-status'); el.textContent = message;
}
function copyRich() {
 const article = document.getElementById('wechat-article');
 const selection = window.getSelection(); const range = document.createRange();
 range.selectNodeContents(article); selection.removeAllRanges(); selection.addRange(range);
 let ok = false;
 try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
 selection.removeAllRanges();
 showStatus(ok ? '已复制正文；请粘贴后在公众号编辑器预览检查。' : '浏览器未允许自动复制，请手动选中正文复制。');
}
async function copyPlain() {
 const text = document.getElementById('wechat-article').innerText;
 let ok = false;
 if (navigator.clipboard && navigator.clipboard.writeText) {
  try { await navigator.clipboard.writeText(text); ok = true; } catch (_) { }
 }
 if (!ok) {
   const t = document.createElement('textarea'); t.value=text; t.style.position='fixed'; t.style.opacity='0';
   document.body.appendChild(t); t.select();
   try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
   t.remove();
 }
 showStatus(ok ? '已复制纯文本。' : '复制被限制，请手动复制正文。');
}
"""


def render_document(markdown: str, cover_data_uri: str | None = None, account_name: str = "小康新鲜事儿") -> str:
    title, content = parse_markdown(markdown)
    count = len(re.sub(r"[#*\s`>\-]", "", markdown))
    cover = ('<img class="cover-preview" alt="文章封面预览" src="' + html.escape(cover_data_uri, quote=True) + '" />') if cover_data_uri else ""
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light"><title>""" + html.escape(title) + " · 公众号离线预览</title>\n<style>" + STYLE + "</style></head><body>\n" + """
<div class="toolbar"><div class="toolbar-inner"><span class="brand">小康新鲜事儿 · 离线排版预览</span>
<button class="primary" type="button" onclick="copyRich()">复制排版正文</button>
<button type="button" onclick="copyPlain()">复制纯文本</button>
<button type="button" onclick="window.print()">打印 / 存为 PDF</button></div></div>
<main class="wrap"><section class="paper"><header class="hero">""" + cover + """<div class="eyebrow">WECHAT ARTICLE / DRAFT</div><h1>""" + html.escape(title) + "</h1><div class=\"hero-meta\"><span>演示稿 · 未经作者确认</span><span>约 " + str(count) + " 字</span><span>仅本地预览，未发布</span></div></header><article id=\"wechat-article\" class=\"content\">\n" + content + "\n</article></section><p class=\"note\">预览文件不联网，不会自动发布。复制正文后请在公众号编辑器检查手机端效果。<br><span id=\"copy-status\" class=\"status\" role=\"status\"></span></p></main><script>" + JS + "</script></body></html>\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a Markdown article to a standalone offline HTML preview.")
    parser.add_argument("input", type=pathlib.Path, help="Markdown input file (UTF-8)")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="Output HTML path")
    parser.add_argument("--cover", type=pathlib.Path, help="Local PNG/JPEG/WebP image file; embedded as offline data URI")
    args = parser.parse_args(argv)
    if not args.input.is_file():
        parser.error(f"Article not found: {args.input}")
    raw = args.input.read_text(encoding="utf-8-sig")
    if not raw.strip():
        parser.error("Article is empty")
    target = args.output or args.input.with_suffix(".html")
    target.parent.mkdir(parents=True, exist_ok=True)
    cover_data_uri = None
    if args.cover:
        if not args.cover.is_file():
            parser.error(f"Cover image not found: {args.cover}")
        kind = args.cover.suffix.lower()
        types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        if kind not in types:
            parser.error("--cover must be a local PNG/JPEG/WebP file")
        cover_data_uri = "data:" + types[kind] + ";base64," + base64.b64encode(args.cover.read_bytes()).decode("ascii")
    target.write_text(render_document(raw, cover_data_uri=cover_data_uri), encoding="utf-8")
    print(f"[OK] HTML preview: {target} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
