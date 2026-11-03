#!/usr/bin/env python3
"""
GHEBRES OFFICIAL renderer: JSON spec -> branded PNG (Persian, RTL).

Usage:
    python3 render.py spec.json -o out_dir
    python3 render.py spec.json -o out_dir --html-only   # write HTML, skip PNG

Layouts: news, list, breaking, quote
Formats: story (1080x1920), post (1080x1350), square (1080x1080)

Long lists are split into several pages automatically (out_1.png, out_2.png ...).
"""
import argparse
import base64
import html
import json
import math
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "assets" / "fonts"
DEFAULT_LOGO = HERE.parent / "assets" / "logo.png"

# ---- Brand tokens (edit here to change the whole brand) --------------------
BRAND = {
    "navy_deep": "#050E1C",
    "navy": "#0A1A30",
    "navy_soft": "#13284A",
    "gold": "#D6B04C",
    "gold_soft": "#EBD08A",
    "gold_dim": "#8C7428",
    "text": "#F4F1E8",
    "text_dim": "#A9B4C6",
    "red": "#C0392B",
    "handle": "@ghebres_official",
    "telegram": "t.me/ghebres_official",
    "wordmark": "GHEBRES",
    "wordmark_sub": "OFFICIAL",
}

FORMATS = {
    "story": (1080, 1920),
    "post": (1080, 1350),
    "square": (1080, 1080),
}

# items per page for list layout, by format
LIST_CAP = {"story": 5, "post": 3, "square": 2}

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(s, enable=True):
    if s is None:
        return ""
    s = str(s)
    if not enable:
        return s
    # only localize digits in text that contains Persian/Arabic letters,
    # so Latin addresses ("No:12") and codes stay as they are
    if any("\u0600" <= ch <= "\u06FF" for ch in s) or s.strip().isdigit():
        return s.translate(FA_DIGITS)
    return s


def esc(s, digits=True):
    return html.escape(fa(s, digits))


def font_face():
    weights = {"Regular": 400, "Medium": 500, "Bold": 700, "Black": 900}
    out = []
    for name, w in weights.items():
        p = FONTS / f"Vazirmatn-{name}.ttf"
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'Vazirmatn';font-weight:{w};"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}"
        )
    return "\n".join(out)


def img_data_uri(path):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        print(f"warning: image not found: {path}", file=sys.stderr)
        return None
    ext = p.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "png")
    return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def base_css(w, h):
    B = BRAND
    s = w / 1080  # scale factor
    return f"""
{font_face()}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{w}px;height:{h}px;overflow:hidden}}
body{{font-family:'Vazirmatn',sans-serif;direction:rtl;color:{B['text']};
  background:radial-gradient(120% 80% at 50% 0%, {B['navy_soft']} 0%, {B['navy']} 45%, {B['navy_deep']} 100%);
  position:relative}}
.frame{{position:absolute;inset:{28*s}px;border:{2*s}px solid {B['gold_dim']};border-radius:{18*s}px;pointer-events:none}}
.corner{{position:absolute;width:{70*s}px;height:{70*s}px;border-color:{B['gold']};border-style:solid;border-width:0}}
.c-tr{{top:{20*s}px;right:{20*s}px;border-top-width:{5*s}px;border-right-width:{5*s}px;border-top-right-radius:{20*s}px}}
.c-tl{{top:{20*s}px;left:{20*s}px;border-top-width:{5*s}px;border-left-width:{5*s}px;border-top-left-radius:{20*s}px}}
.c-br{{bottom:{20*s}px;right:{20*s}px;border-bottom-width:{5*s}px;border-right-width:{5*s}px;border-bottom-right-radius:{20*s}px}}
.c-bl{{bottom:{20*s}px;left:{20*s}px;border-bottom-width:{5*s}px;border-left-width:{5*s}px;border-bottom-left-radius:{20*s}px}}
.wrap{{position:absolute;inset:{70*s}px {72*s}px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center;direction:ltr}}
.wm{{font-family:'Vazirmatn';font-weight:900;letter-spacing:{6*s}px;font-size:{44*s}px;color:{B['gold']};line-height:1}}
.wm small{{display:block;font-weight:500;letter-spacing:{11*s}px;font-size:{17*s}px;color:{B['gold_soft']};margin-top:{6*s}px}}
.brand{{display:flex;align-items:center;gap:{20*s}px}}
.logo{{height:{104*s}px;filter:drop-shadow(0 0 {10*s}px rgba(212,175,55,.25))}}
.date{{direction:rtl;font-weight:500;font-size:{28*s}px;color:{B['text_dim']}}}
.rule{{height:{3*s}px;margin:{34*s}px 0;background:linear-gradient(90deg,transparent,{B['gold']},transparent)}}
.badge{{align-self:flex-start;background:{B['gold']};color:{B['navy_deep']};font-weight:900;
  font-size:{30*s}px;padding:{10*s}px {30*s}px;border-radius:{40*s}px}}
.badge.red{{background:{B['red']};color:#fff}}
.title{{font-weight:900;color:{B['text']};line-height:1.45;margin-top:{30*s}px}}
.title .g{{color:{B['gold']}}}
.sub{{font-weight:500;color:{B['gold_soft']};font-size:{34*s}px;margin-top:{16*s}px;line-height:1.6}}
.body{{font-weight:400;color:{B['text']};font-size:{38*s}px;line-height:1.85;margin-top:{30*s}px;text-align:justify}}
.body p+p{{margin-top:{18*s}px}}
.hero{{width:100%;border-radius:{18*s}px;border:{3*s}px solid {B['gold_dim']};object-fit:cover;margin-top:{30*s}px}}
.grow{{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column}}
.foot{{margin-top:auto;padding-top:{26*s}px;display:flex;justify-content:space-between;align-items:center;
  border-top:{2*s}px solid {B['gold_dim']};font-size:{27*s}px;color:{B['text_dim']};direction:ltr}}
.foot b{{color:{B['gold']};font-weight:700}}
.src{{direction:rtl;unicode-bidi:isolate}}
.page{{direction:rtl;color:{B['gold_soft']};font-weight:700}}
/* list */
.items{{display:flex;flex-direction:column;gap:{22*s}px;margin-top:{30*s}px}}
.item{{display:flex;gap:{26*s}px;align-items:stretch;background:rgba(255,255,255,0.035);
  border:{2*s}px solid rgba(212,175,55,0.35);border-radius:{18*s}px;padding:{24*s}px {28*s}px}}
.num{{flex:0 0 auto;min-width:{84*s}px;display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:{44*s}px;color:{B['navy_deep']};background:{B['gold']};border-radius:{14*s}px}}
.it-main{{flex:1;min-width:0}}
.it-t{{font-weight:700;font-size:{38*s}px;color:{B['text']};line-height:1.45}}
.it-s{{font-weight:400;font-size:{29*s}px;color:{B['text_dim']};line-height:1.6;margin-top:{6*s}px}}
.it-m{{font-weight:700;font-size:{30*s}px;color:{B['gold_soft']};margin-top:{8*s}px;direction:rtl}}
.it-m .ltr{{direction:ltr;unicode-bidi:isolate}}
.tag{{flex:0 0 auto;align-self:center;font-weight:700;font-size:{26*s}px;color:{B['gold']};
  border:{2*s}px solid {B['gold']};border-radius:{30*s}px;padding:{6*s}px {18*s}px}}
/* breaking */
.breaking .title{{text-align:center}}
.center{{flex:1;display:flex;flex-direction:column;justify-content:center}}
/* quote */
.qmark{{font-size:{220*s}px;line-height:.8;color:{B['gold']};font-weight:900;font-family:'Vazirmatn'}}
.qby{{margin-top:{30*s}px;font-size:{34*s}px;color:{B['gold_soft']};font-weight:700}}
"""


def header(spec, s):
    logo_path = spec.get("logo") or (DEFAULT_LOGO if DEFAULT_LOGO.exists() else None)
    logo = img_data_uri(logo_path) if spec.get("logo") is not False else None
    wm = f'<div class="wm">{BRAND["wordmark"]}<small>{BRAND["wordmark_sub"]}</small></div>'
    left = f'<div class="brand"><img class="logo" src="{logo}">{wm}</div>' if logo else wm
    date = esc(spec.get("date", ""), spec.get("persian_digits", True))
    return f'<div class="top">{left}<div class="date">{date}</div></div><div class="rule"></div>'


def footer(spec, page=None, pages=None):
    d = spec.get("persian_digits", True)
    src = spec.get("source")
    src_html = f'<span class="src">منبع: {esc(src, d)}</span>' if src else ""
    pg = ""
    if pages and pages > 1:
        pg = f'<span class="page">{fa(page, d)} / {fa(pages, d)}</span>'
    mid = src_html or pg
    if src_html and pg:
        mid = f"{src_html}&nbsp;&nbsp;·&nbsp;&nbsp;{pg}"
    return (f'<div class="foot"><span><b>{BRAND["handle"]}</b></span>'
            f'{mid}<span>{BRAND["telegram"]}</span></div>')


def title_html(t, d):
    # *word* -> gold highlight
    t = esc(t, d)
    parts = t.split("*")
    return "".join(f'<span class="g">{p}</span>' if i % 2 else p for i, p in enumerate(parts))


def page_shell(w, h, inner, extra_class=""):
    return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<style>{base_css(w, h)}</style></head>
<body class="{extra_class}"><div class="frame"></div>
<div class="corner c-tr"></div><div class="corner c-tl"></div><div class="corner c-br"></div><div class="corner c-bl"></div>
<div class="wrap">{inner}</div>
<script>
// shrink-to-fit for title and body
function fit(sel, max, min){{
  document.querySelectorAll(sel).forEach(el=>{{
    let size=max; el.style.fontSize=size+'px';
    const box=el.closest('.grow')||document.querySelector('.wrap');
    while(size>min && (box.scrollHeight>box.clientHeight+1)){{size-=2; el.style.fontSize=size+'px';}}
  }});
}}
document.fonts.ready.then(()=>{{
  fit('.title', parseFloat(document.body.dataset.tmax||90), 44);
  fit('.body', parseFloat(document.body.dataset.bmax||38), 26);
  document.body.setAttribute('data-ready','1');
}});
</script></body></html>"""


def layout_news(spec, fmt):
    w, h = FORMATS[fmt]
    s = w / 1080
    d = spec.get("persian_digits", True)
    badge = spec.get("category")
    hero = img_data_uri(spec.get("image"))
    hero_h = {"story": 640, "post": 430, "square": 0}[fmt] * s
    body = spec.get("body", "")
    paras = body if isinstance(body, list) else [p for p in str(body).split("\n") if p.strip()]
    body_html = "".join(f"<p>{esc(p, d)}</p>" for p in paras)
    inner = header(spec, s)
    inner += '<div class="grow">'
    if badge:
        inner += f'<div class="badge">{esc(badge, d)}</div>'
    if hero and hero_h:
        inner += f'<img class="hero" style="height:{hero_h}px" src="{hero}">'
    inner += f'<div class="title">{title_html(spec.get("title", ""), d)}</div>'
    if spec.get("subtitle"):
        inner += f'<div class="sub">{esc(spec["subtitle"], d)}</div>'
    if body_html:
        inner += f'<div class="body">{body_html}</div>'
    inner += "</div>" + footer(spec)
    tmax = {"story": 78, "post": 64, "square": 58}[fmt] * s
    html_doc = page_shell(w, h, inner).replace(
        '<body class="">', f'<body class="" data-tmax="{tmax}" data-bmax="{38*s}">')
    return [html_doc]


def layout_list(spec, fmt):
    w, h = FORMATS[fmt]
    s = w / 1080
    d = spec.get("persian_digits", True)
    items = spec.get("items", [])
    cap = int(spec.get("per_page") or LIST_CAP[fmt])
    pages = max(1, math.ceil(len(items) / cap))
    numbered = spec.get("numbered", True)
    docs = []
    for pi in range(pages):
        chunk = items[pi * cap:(pi + 1) * cap]
        rows = []
        for j, it in enumerate(chunk):
            n = pi * cap + j + 1
            num = f'<div class="num">{fa(it.get("rank", n), d)}</div>' if numbered else ""
            meta = ""
            if it.get("meta"):
                meta = f'<div class="it-m">{esc(it["meta"], d)}</div>'
            if it.get("phone"):
                meta += f'<div class="it-m">☎ <span class="ltr">{html.escape(str(it["phone"]))}</span></div>'
            sub = f'<div class="it-s">{esc(it["subtitle"], d)}</div>' if it.get("subtitle") else ""
            tag = f'<div class="tag">{esc(it["tag"], d)}</div>' if it.get("tag") else ""
            rows.append(f'<div class="item">{num}<div class="it-main"><div class="it-t">{esc(it.get("title", ""), d)}</div>{sub}{meta}</div>{tag}</div>')
        inner = header(spec, s)
        inner += '<div class="grow">'
        if spec.get("category"):
            inner += f'<div class="badge">{esc(spec["category"], d)}</div>'
        inner += f'<div class="title">{title_html(spec.get("title", ""), d)}</div>'
        if spec.get("subtitle"):
            inner += f'<div class="sub">{esc(spec["subtitle"], d)}</div>'
        inner += f'<div class="items">{"".join(rows)}</div></div>'
        inner += footer(spec, pi + 1, pages)
        tmax = {"story": 64, "post": 54, "square": 48}[fmt] * s
        docs.append(page_shell(w, h, inner).replace(
            '<body class="">', f'<body class="" data-tmax="{tmax}" data-bmax="{38*s}">'))
    return docs


def layout_breaking(spec, fmt):
    w, h = FORMATS[fmt]
    s = w / 1080
    d = spec.get("persian_digits", True)
    inner = header(spec, s) + '<div class="grow center">'
    inner += f'<div class="badge red" style="align-self:center">{esc(spec.get("category") or "خبر فوری", d)}</div>'
    inner += f'<div class="title">{title_html(spec.get("title", ""), d)}</div>'
    if spec.get("subtitle"):
        inner += f'<div class="sub" style="text-align:center">{esc(spec["subtitle"], d)}</div>'
    inner += "</div>" + footer(spec)
    tmax = {"story": 96, "post": 80, "square": 72}[fmt] * s
    return [page_shell(w, h, inner, "breaking").replace(
        '<body class="breaking">', f'<body class="breaking" data-tmax="{tmax}">')]


def layout_quote(spec, fmt):
    w, h = FORMATS[fmt]
    s = w / 1080
    d = spec.get("persian_digits", True)
    inner = header(spec, s) + '<div class="grow center">'
    inner += '<div class="qmark">«</div>'
    inner += f'<div class="title">{title_html(spec.get("title", ""), d)}</div>'
    if spec.get("by"):
        inner += f'<div class="qby">— {esc(spec["by"], d)}</div>'
    inner += "</div>" + footer(spec)
    tmax = {"story": 70, "post": 60, "square": 54}[fmt] * s
    return [page_shell(w, h, inner).replace('<body class="">', f'<body class="" data-tmax="{tmax}">')]


LAYOUTS = {"news": layout_news, "list": layout_list, "breaking": layout_breaking, "quote": layout_quote}

# light Mediterranean trilingual theme (story only)
sys.path.insert(0, str(HERE))
import light  # noqa: E402

LIGHT = light.make({
    "font_face": font_face(),
    "img": img_data_uri,
    "logo_uri": img_data_uri(DEFAULT_LOGO) if DEFAULT_LOGO.exists() else None,
})
LAYOUTS.update(LIGHT)


def find_chrome():
    for c in [os.environ.get("CHROME_PATH"), "/usr/bin/google-chrome", "/usr/bin/chromium",
              "/usr/bin/chromium-browser",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"]:
        if c and Path(c).exists():
            return c
    return shutil.which("google-chrome") or shutil.which("chromium")


def to_png(html_files, w, h):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright missing: pip install playwright && python -m playwright install chromium")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            exe = find_chrome()
            if not exe:
                raise
            browser = p.chromium.launch(executable_path=exe)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        outs = []
        for hf in html_files:
            page.goto(Path(hf).resolve().as_uri())
            page.wait_for_selector("body[data-ready='1']", timeout=15000)
            png = str(Path(hf).with_suffix(".png"))
            page.screenshot(path=png, full_page=False)
            outs.append(png)
        browser.close()
    return outs


def render(specs, out, html_only=False):
    """Render a list of spec dicts into out/; returns list of produced file paths."""
    specs = specs if isinstance(specs, list) else [specs]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    produced = []
    for k, sp in enumerate(specs):
        fmt = sp.get("format", "story")
        lay = sp.get("layout", "news")
        if lay in LIGHT:
            fmt = "story"
        if fmt not in FORMATS or lay not in LAYOUTS:
            raise ValueError(f"bad format/layout: {fmt}/{lay}")
        name = sp.get("name") or f"{lay}_{fmt}_{k+1}"
        docs = LAYOUTS[lay](sp, fmt)
        files = []
        for i, doc in enumerate(docs):
            suffix = f"_{i+1}" if len(docs) > 1 else ""
            f = out / f"{name}{suffix}.html"
            f.write_text(doc, encoding="utf-8")
            files.append(f)
        if html_only:
            produced += [str(f) for f in files]
        else:
            produced += to_png(files, *FORMATS[fmt])
            for f in files:
                f.unlink()
    return produced


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default="out")
    ap.add_argument("--html-only", action="store_true")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    try:
        produced = render(spec, a.out, a.html_only)
    except ValueError as ex:
        sys.exit(str(ex))
    print("\n".join(produced))


if __name__ == "__main__":
    main()
