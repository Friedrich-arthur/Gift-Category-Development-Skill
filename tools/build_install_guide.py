"""Render the public installation guide from its Markdown source."""

import argparse
from html import escape
import sys
from pathlib import Path

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/INSTALLATION.md"
TARGET = ROOT / "docs/site/install.html"

STYLE = """
*{box-sizing:border-box}html,body{overflow-x:clip}html{scroll-behavior:smooth;scroll-padding-top:88px}
body{margin:0;background:var(--color-paper);color:var(--color-ink);font:var(--text-body)/1.85 var(--font-body);-webkit-font-smoothing:antialiased}
a{color:var(--color-accent);text-underline-offset:4px;overflow-wrap:anywhere}a:hover{text-decoration-thickness:2px}
a:focus-visible,button:focus-visible{outline:3px solid var(--color-focus);outline-offset:4px}
.wrap{width:min(1200px,calc(100% - 80px));margin:auto}.top{display:flex;justify-content:space-between;gap:20px;align-items:center;padding-block:24px;border-bottom:1px solid var(--color-rule)}
.brand{color:var(--color-ink);font-weight:750;text-decoration:none}.top>a:last-child{font-size:.9rem}.skip{position:absolute;top:8px;left:8px;transform:translateY(-180%);padding:8px 16px;background:var(--color-accent);color:var(--color-paper);z-index:10}.skip:focus{transform:none}
.intro{padding-block:48px 32px;display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:40px;align-items:center}.eyebrow{color:var(--color-accent);font-size:.9rem;letter-spacing:.08em;margin:0 0 16px}.intro h1{font:850 clamp(2.4rem,4.6vw,4.5rem)/1.2 var(--font-display);letter-spacing:-.05em;margin:0 0 24px;max-width:12em}.intro p{color:var(--color-muted);max-width:39em}.intro img{width:100%;border:1px solid var(--color-rule);border-radius:var(--radius-md)}
.jump{position:sticky;top:0;background:var(--color-paper);border-block:1px solid var(--color-rule);z-index:2}.jump .wrap{display:flex;gap:8px;padding-block:12px;flex-wrap:wrap}.jump a{padding:7px 14px;border:1px solid var(--color-rule);border-radius:var(--radius-sm);text-decoration:none;color:var(--color-ink);font-weight:650}.jump a:nth-child(-n+3){border-color:var(--color-accent);color:var(--color-accent)}.jump a:hover{background:var(--color-surface)}
.layout{display:grid;grid-template-columns:minmax(0,820px) minmax(180px,1fr);gap:64px;padding-block:40px 72px}.guide{min-width:0}.guide>p:first-child{margin-top:0}.guide h2{font:800 clamp(1.8rem,3vw,2.6rem)/1.3 var(--font-display);letter-spacing:-.035em;margin:64px 0 24px;padding-top:32px;border-top:1px solid var(--color-rule)}.guide h2:first-of-type{margin-top:0}.guide h3{font-size:1.2rem;margin:32px 0 16px}.guide p{margin:16px 0}.guide li{padding-left:5px;margin-block:14px}.guide ol,.guide ul{padding-left:1.6em}.guide ol li::marker{color:var(--color-accent);font-weight:750}.guide img{width:100%;max-width:640px;height:auto;border-radius:var(--radius-md);margin-block:12px}
code{font-family:var(--font-mono);font-size:.88em;overflow-wrap:anywhere}p code,li code,td code{color:var(--color-ink);background:var(--color-surface);padding:2px 5px;border-radius:4px}pre{background:var(--color-surface);border:1px solid var(--color-rule);padding:24px;border-radius:var(--radius-md);margin:24px 0;white-space:pre-wrap;overflow-wrap:anywhere;tab-size:4}pre code{font-size:.9rem;line-height:1.85;white-space:pre-wrap}
.copy-tools{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin:-12px 0 28px}.copy-tools button{font:650 .9rem var(--font-body);min-height:44px;padding:10px 16px;border:1px solid var(--color-accent);border-radius:var(--radius-sm);color:var(--color-accent);background:var(--color-paper);cursor:pointer}.copy-status{font-size:.85rem;color:var(--color-muted)}
.table-wrap{overflow-x:auto;margin-block:24px}table{border-collapse:collapse;width:100%;font-size:.95rem}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--color-rule);padding:16px 12px}th{color:var(--color-accent)}th:first-child,td:first-child{width:35%;min-width:155px}td{min-width:220px}
.side{font-size:.9rem;color:var(--color-muted)}.side>div{position:sticky;top:105px;border-left:1px solid var(--color-rule);padding-left:24px}.side p{margin:0 0 16px}.side nav{display:grid;gap:12px}.side a{color:var(--color-muted)}.side strong{color:var(--color-ink)}footer{border-top:1px solid var(--color-rule);padding-block:24px 32px;display:flex;justify-content:space-between;gap:20px;color:var(--color-muted);font-size:.85rem}::selection{background:var(--color-accent);color:var(--color-paper)}
@media(max-width:900px){.layout{grid-template-columns:minmax(0,1fr);gap:0}.side{display:none}.intro{grid-template-columns:minmax(0,1fr) 220px;gap:24px}}
@media(max-width:620px){html{scroll-padding-top:136px}.wrap{width:calc(100% - 40px)}.top{padding-block:16px;align-items:flex-start}.brand{font-size:.85rem}.top>a:last-child{font-size:.8rem;white-space:nowrap}.intro{grid-template-columns:1fr;padding-block:32px 24px;gap:12px}.intro h1{font-size:2.6rem}.intro img{width:180px;justify-self:end;display:none}.jump .wrap{gap:7px;padding-block:10px}.jump a{font-size:.85rem;padding:6px 10px;min-height:40px;display:flex;align-items:center}.layout{padding-block:32px 48px}.guide h2{margin-top:48px;padding-top:24px}.guide ol,.guide ul{padding-left:1.35em}.guide li{margin-block:16px}pre{padding:16px}pre code{font-size:.85rem}th:first-child,td:first-child{min-width:0;width:35%}td{min-width:0;overflow-wrap:anywhere}th,td{padding:12px 8px}footer{flex-direction:column;gap:8px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{.jump,.side,.copy-tools,.intro img{display:none}.wrap{width:100%}.layout{display:block}.intro{display:block}body{background:white;color:black}a{color:inherit}pre{background:#f4f4f4}.guide h2{break-after:avoid}}
"""

SCRIPT = """
document.querySelectorAll('pre code.language-text').forEach((code, index) => {
  const pre = code.parentElement;
  const tools = document.createElement('div');
  tools.className = 'copy-tools';
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = '复制这段文字';
  const status = document.createElement('span');
  status.className = 'copy-status';
  status.id = 'copy-status-' + index;
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  button.setAttribute('aria-describedby', status.id);
  tools.append(button, status);
  pre.after(tools);
  button.addEventListener('click', async () => {
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('manual');
      await navigator.clipboard.writeText(pre.textContent.trim());
      status.textContent = '已复制，去对应工具里粘贴。';
    } catch {
      const selection = window.getSelection();
      if (selection) {
        const range = document.createRange();
        range.selectNodeContents(pre);
        selection.removeAllRanges();
        selection.addRange(range);
      }
      status.textContent = '请长按选中文字复制，或按 Ctrl/Cmd+C。';
    }
  });
});
"""


def render() -> str:
    markdown = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = markdown.parse(SOURCE.read_text(encoding="utf-8"))
    title = tokens[1].content
    for token in tokens:
        for child in token.children or []:
            if child.type == "image":
                path = child.attrGet("src") or ""
                if path.startswith("site/assets/"):
                    child.attrSet("src", path.removeprefix("site/"))
    body_start = next(
        index - 1 for index, token in enumerate(tokens)
        if token.type == "inline" and 'id="download"' in token.content
    )
    body = markdown.renderer.render(tokens[body_start:], markdown.options, {})
    title_html = escape(title).replace("，", "，<br>", 1)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )
    return f'''<!doctype html>
<!-- Generated by tools/build_install_guide.py from docs/INSTALLATION.md. -->
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="礼品开发 Skill 完整安装指引。WorkBuddy、豆包工作和 Codex 的下载、导入、开始使用、升级、卸载与常见问题。">
<meta name="theme-color" content="#171512">
<title>{title}｜礼品开发 Skill 安装指引</title>
<link rel="icon" href="assets/cover.svg" type="image/svg+xml">
<link rel="stylesheet" href="tokens.css">
<style>{STYLE}
.intro img{{height:auto}}
</style>
</head>
<body>
<a class="skip" href="#guide">跳到安装正文</a>
<header class="top wrap"><a class="brand" href="index.html">海外礼品经营判断 Skill</a><a href="index.html">回到首页 ↗</a></header>
<div class="intro wrap"><div><p class="eyebrow">0.6.0 · 完整安装指引</p><h1>{title_html}</h1><p>你用哪个工具，就看哪一段。下载的是同一个包，装好后直接聊自己的产品。</p></div><img src="assets/cover.svg" alt="橙色礼盒与下一款礼品做什么的提问" width="1600" height="840"></div>
<nav class="jump" aria-label="按工具查看安装步骤"><div class="wrap"><a href="#workbuddy">WorkBuddy</a><a href="#doubao">豆包工作</a><a href="#codex">Codex</a><a href="#download">下载</a><a href="#start">开始使用</a><a href="#update">升级</a><a href="#help">装不上？</a></div></nav>
<main class="layout wrap" id="guide"><article class="guide" aria-label="完整安装步骤">{body}</article>
<aside class="side"><div><p><strong>只看自己用的工具。</strong></p><p>先下载，再导入。看到技能后，新开对话选中它，拿一款产品试一次。</p><nav aria-label="其他安装事项"><a href="#update">升级与卸载</a><a href="#agent">让代理代装</a><a href="#help">常见问题</a><a href="#sources">指引依据与边界</a><a href="https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/blob/main/docs/INSTALLATION.md">在 GitHub 看文字版 ↗</a></nav></div></aside></main>
<footer class="wrap"><span>海外礼品经营判断 · gift-development-service</span><a href="index.html">回首页，看能怎么用 ↗</a></footer>
<script>{SCRIPT}</script>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated HTML is stale.")
    args = parser.parse_args()
    result = render()
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != result:
            print("Installation HTML is stale. Run python tools/build_install_guide.py.", file=sys.stderr)
            return 1
        print("Installation guide is synchronized.")
        return 0
    TARGET.write_text(result, encoding="utf-8", newline="\n")
    print("Built docs/site/install.html from docs/INSTALLATION.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
