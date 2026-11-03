"""
GHEBRES light "Mediterranean" theme: trilingual (TR / EN / FA) story layouts.

Layouts: weather, news3, pharmacy   (story format, 1080x1920)
Imported by render.py.
"""
import datetime as dt
import html
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "photos"

L = {
    "navy": "#0E2F6E",
    "blue": "#1565C0",
    "sky": "#BFE3F7",
    "ink": "#1D2B44",
    "muted": "#5B6B85",
    "red": "#E53935",
    "gold": "#B68A2C",
    "card": "rgba(255,255,255,0.90)",
    "tg": "#29A9EB",
}

CITIES = {
    "lefkosa": {"en": "Nicosia", "tr": "Lefkoşa", "fa": "نیکوزیا", "color": "#1E5BD8"},
    "girne": {"en": "Kyrenia", "tr": "Girne", "fa": "گیرنه", "color": "#12A79D"},
    "magusa": {"en": "Famagusta", "tr": "Gazimağusa", "fa": "فاماگوستا", "color": "#F28C28"},
    "iskele": {"en": "Iskele", "tr": "İskele", "fa": "ایسکله", "color": "#7B3FD1"},
    "guzelyurt": {"en": "Morphou", "tr": "Güzelyurt", "fa": "گوزل‌یورت", "color": "#1FA37A"},
    "lefke": {"en": "Lefka", "tr": "Lefke", "fa": "لفکه", "color": "#E2508C"},
    "karpaz": {"en": "Karpas", "tr": "Karpaz", "fa": "کارپاز", "color": "#E0A410"},
    "ustmesarya": {"en": "Upper Mesaoria", "tr": "Üst Mesarya", "fa": "مسارئای شمالی", "color": "#6D8B1E"},
    "altmesarya": {"en": "Lower Mesaoria", "tr": "Alt Mesarya", "fa": "مسارئای جنوبی", "color": "#8A5A2B"},
}
CITY_ALIASES = {
    "nicosia": "lefkosa", "lefkoşa": "lefkosa", "kyrenia": "girne", "famagusta": "magusa",
    "gazimagusa": "magusa", "gazimağusa": "magusa", "mağusa": "magusa", "İskele": "iskele",
    "trikomo": "iskele", "morphou": "guzelyurt", "güzelyurt": "guzelyurt", "lefka": "lefke",
    "karpas": "karpaz",
}

CONDITIONS = {
    "sunny": ("Sunny", "Güneşli", "آفتابی"),
    "partly": ("Partly Cloudy", "Parçalı Bulutlu", "نیمه‌ابری"),
    "cloudy": ("Cloudy", "Bulutlu", "ابری"),
    "rain": ("Rainy", "Yağmurlu", "بارانی"),
    "storm": ("Thunderstorm", "Gök Gürültülü", "رعد و برق"),
    "fog": ("Foggy", "Sisli", "مه‌آلود"),
    "wind": ("Windy", "Rüzgarlı", "وزش باد"),
}

FA_DIG = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
TR_M = "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split()
TR_D = "Pazartesi Salı Çarşamba Perşembe Cuma Cumartesi Pazar".split()
EN_M = "January February March April May June July August September October November December".split()
EN_D = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
FA_M = "فروردین اردیبهشت خرداد تیر مرداد شهریور مهر آبان آذر دی بهمن اسفند".split()
FA_D = "دوشنبه سه‌شنبه چهارشنبه پنجشنبه جمعه شنبه یکشنبه".split()


def e(s):
    return html.escape("" if s is None else str(s))


def fa_num(s):
    return str(s).translate(FA_DIG)


def g2j(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def dates(spec):
    """Return (tr, en, fa) date strings. Uses spec['date'] = 'YYYY-MM-DD' or explicit date_tr/en/fa."""
    d = spec.get("date")
    out = {"tr": spec.get("date_tr"), "en": spec.get("date_en"), "fa": spec.get("date_fa")}
    try:
        g = dt.date.fromisoformat(str(d)) if d else None
    except ValueError:
        g = None
    if g:
        wd = g.weekday()
        jy, jm, jd = g2j(g.year, g.month, g.day)
        out["tr"] = out["tr"] or f"{g.day} {TR_M[g.month-1]} {g.year} ({TR_D[wd]})"
        out["en"] = out["en"] or f"{EN_M[g.month-1]} {g.day}, {g.year} ({EN_D[wd]})"
        out["fa"] = out["fa"] or fa_num(f"{FA_D[wd]} {jd} {FA_M[jm-1]} {jy}")
    elif d and not any(out.values()):
        out["fa"] = fa_num(d)
    return out["tr"], out["en"], out["fa"]


def city(key_or_name):
    k = str(key_or_name or "").strip()
    kl = k.lower()
    kl = CITY_ALIASES.get(kl, CITY_ALIASES.get(k, kl))
    c = CITIES.get(kl)
    if c:
        return kl, c
    return None, {"en": k, "tr": k, "fa": k, "color": L["blue"]}


# ---------------------------------------------------------------- icons
def svg(body, vb="0 0 24 24", cls="ic", fill="currentColor"):
    return f'<svg class="{cls}" viewBox="{vb}" fill="{fill}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


PIN = svg('<path d="M12 2C8 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3-7-7-7zm0 9.6A2.6 2.6 0 1 1 12 6.4a2.6 2.6 0 0 1 0 5.2z"/>')
PHONE = svg('<path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25c1.1.37 2.3.57 3.6.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/>')
CAL = svg('<path d="M7 2v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2V2h-2v2H9V2zm-2 7h14v11H5zm2 2v2h2v-2zm4 0v2h2v-2zm4 0v2h2v-2zm-8 4v2h2v-2zm4 0v2h2v-2zm4 0v2h2v-2z"/>')
TG_PLANE = '<path d="M9.8 15.6 9.4 20c.6 0 .9-.3 1.2-.6l2.9-2.7 6 4.4c1.1.6 1.9.3 2.2-1L24 3.6c.4-1.6-.6-2.2-1.6-1.8L1.1 10c-1.5.6-1.5 1.4-.3 1.8l5.6 1.7 12.9-8.2c.6-.4 1.2-.2.7.3z"/>'
TG = f'<div class="tg-ic">{svg(TG_PLANE, "-1 -1 26 26", "ic", "#fff")}</div>'


def weather_icon(kind):
    sun = ('<g><circle cx="32" cy="32" r="13" fill="url(#sg)"/>'
           + "".join(f'<rect x="30.5" y="5" width="3" height="9" rx="1.5" fill="#F6B21B" transform="rotate({a} 32 32)"/>'
                     for a in range(0, 360, 45)) + "</g>")
    defs = ('<defs><radialGradient id="sg" cx="40%" cy="35%"><stop offset="0" stop-color="#FFE27A"/>'
            '<stop offset="1" stop-color="#F5A70F"/></radialGradient>'
            '<linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EAF6FF"/>'
            '<stop offset="1" stop-color="#9FCBEF"/></linearGradient>'
            '<linearGradient id="gg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F2F4F7"/>'
            '<stop offset="1" stop-color="#B9C2CE"/></linearGradient></defs>')

    def cloud(fill, dx=0, dy=0, s=1):
        return (f'<g transform="translate({dx} {dy}) scale({s})" fill="{fill}">'
                '<circle cx="26" cy="38" r="11"/><circle cx="38" cy="32" r="13"/><circle cx="48" cy="40" r="9"/>'
                '<rect x="15" y="38" width="42" height="11" rx="5.5"/></g>')
    if kind == "sunny":
        body = sun
    elif kind == "partly":
        body = f'<g transform="translate(-8 -8) scale(.85)">{sun}</g>' + cloud("url(#cg)", 6, 6, .9)
    elif kind == "cloudy":
        body = cloud("url(#gg)", 0, 0, 1.05)
    elif kind == "rain":
        body = cloud("url(#gg)", 0, -6) + "".join(
            f'<path d="M{x} 52l-3 7" stroke="#2F8FE0" stroke-width="3" stroke-linecap="round"/>' for x in (26, 36, 46))
    elif kind == "storm":
        body = cloud("url(#gg)", 0, -6) + '<path d="M36 45l-7 10h6l-4 9 10-13h-6l4-6z" fill="#F6B21B"/>'
    elif kind == "fog":
        body = cloud("url(#gg)", 0, -6) + "".join(
            f'<rect x="14" y="{y}" width="38" height="3" rx="1.5" fill="#B9C2CE"/>' for y in (52, 58))
    elif kind == "wind":
        body = ('<path d="M8 26h30a6 6 0 1 0-6-6M8 36h40a6 6 0 1 1-6 6M8 46h22" stroke="#7FB3E0" '
                'stroke-width="4" fill="none" stroke-linecap="round"/>')
    else:
        body = sun
    return f'<svg class="wx" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">{defs}{body}</svg>'


TOPIC = {
    "news": '<path d="M4 5h13v14H6a2 2 0 0 1-2-2zm13 4h3v8a2 2 0 0 1-2 2h-1zM6 7v3h9V7zm0 5v1.5h9V12zm0 3v1.5h9V15z"/>',
    "ship": '<path d="M4 15l1.5-5H8V6h3V4h2v2h3v4h2.5L20 15c-1 0-2 .6-2.7 1.3C16.6 15.6 15.6 15 14.6 15s-2 .6-2.6 1.3C11.4 15.6 10.4 15 9.4 15s-2 .6-2.7 1.3C6 15.6 5 15 4 15zm6-7v2h4V8zM3 19c1.4 0 2.5-.8 3-1.5.6.7 1.7 1.5 3 1.5s2.4-.8 3-1.5c.6.7 1.7 1.5 3 1.5s2.4-.8 3-1.5c.5.7 1.6 1.5 3 1.5v2c-1.2 0-2.2-.4-3-1-.8.6-1.8 1-3 1s-2.2-.4-3-1c-.8.6-1.8 1-3 1s-2.2-.4-3-1c-.8.6-1.8 1-3 1z"/>',
    "plane": '<path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/>',
    "health": '<path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z"/>',
    "money": '<path d="M3 6h18v12H3zm9 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM5 8v2a2 2 0 0 0 2-2zm12 0a2 2 0 0 0 2 2V8zM5 14v2h2a2 2 0 0 0-2-2zm14 0a2 2 0 0 0-2 2h2z"/>',
    "alert": '<path d="M12 2 1 21h22zm-1 7h2v6h-2zm0 8h2v2h-2z"/>',
    "car": '<path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11v8h-2v-2H7v2H5zm2.2 0h9.6l-1-3H8.2zM7.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm9 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/>',
    "building": '<path d="M4 21V5l8-3v5l8 3v11h-6v-4h-4v4zm3-14v2h2V7zm0 4v2h2v-2zm0 4v2h2v-2zm8-2v2h2v-2zm0 4v2h2v-2z"/>',
}

UK_FLAG = ('<svg viewBox="15 0 30 30" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">'
           '<clipPath id="ukt"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath>'
           '<path d="M0,0v30h60v-30z" fill="#012169"/>'
           '<path d="M0,0L60,30M60,0L0,30" stroke="#fff" stroke-width="6"/>'
           '<path d="M0,0L60,30M60,0L0,30" clip-path="url(#ukt)" stroke="#C8102E" stroke-width="4"/>'
           '<path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/>'
           '<path d="M30,0v30M0,15h60" stroke="#C8102E" stroke-width="6"/></svg>')
IR_FLAG = ('<svg viewBox="0 0 30 30" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">'
           '<rect width="30" height="10" fill="#239F40"/><rect y="10" width="30" height="10" fill="#fff"/>'
           '<rect y="20" width="30" height="10" fill="#DA0000"/></svg>')
TR_FLAG = ('<svg viewBox="0 0 30 30" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">'
           '<rect width="30" height="30" fill="#E30A17"/><circle cx="13" cy="15" r="7" fill="#fff"/>'
           '<circle cx="14.8" cy="15" r="5.6" fill="#E30A17"/>'
           '<path d="M19.2 15l4.4-1.43-2.72 3.74V12.7l2.72 3.74z" fill="#fff"/></svg>')

MORTAR = ('<svg class="mortar" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">'
          '<rect x="62" y="6" width="16" height="52" rx="8" transform="rotate(35 70 32)" fill="#1A4FB0"/>'
          '<path d="M14 50h92c0 26-17 44-46 44S14 76 14 50z" fill="#1E5BD8"/>'
          '<rect x="40" y="94" width="40" height="10" rx="5" fill="#1A4FB0"/>'
          '<path d="M54 58h12v10h10v12H66v10H54V80H44V68h10z" fill="#fff"/>'
          '<g transform="rotate(-40 92 96)"><rect x="78" y="88" width="32" height="15" rx="7.5" fill="#fff" stroke="#1E5BD8" stroke-width="3"/>'
          '<path d="M94 88h8.5a7.5 7.5 0 0 1 0 15H94z" fill="#1E5BD8"/></g></svg>')


# ---------------------------------------------------------------- css
def css(font_face, k=1):
    return f"""
{font_face}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1080px;height:1920px;overflow:hidden}}
body{{font-family:'Vazirmatn',sans-serif;color:{L['ink']};position:relative;
  background:linear-gradient(180deg,#9FD3F2 0%,#CDEBFB 18%,#EEF8FE 42%,#F7FBFE 70%,#E6F3FB 100%)}}
.ltr{{direction:ltr;unicode-bidi:isolate}} .rtl{{direction:rtl;unicode-bidi:isolate}}
.ic{{width:1em;height:1em;flex:0 0 auto}}
.cloud-bg{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(40% 8% at 20% 6%,rgba(255,255,255,.85),transparent 70%),
             radial-gradient(35% 7% at 82% 12%,rgba(255,255,255,.7),transparent 70%),
             radial-gradient(30% 6% at 55% 3%,rgba(255,255,255,.6),transparent 70%)}}
.page{{position:absolute;inset:0;display:flex;flex-direction:column;padding:46px 52px 40px}}
/* top bar: brand at top-right */
.topbar{{display:flex;flex-direction:row-reverse;justify-content:space-between;align-items:center;direction:ltr;min-height:118px}}
.brand{{display:flex;flex-direction:row-reverse;align-items:center;gap:16px}}
.brand img{{height:132px;filter:drop-shadow(0 4px 10px rgba(14,47,110,.25))}}
.brand .nm{{text-align:right;line-height:1}}
.brand .nm b{{display:block;font-weight:900;font-size:44px;letter-spacing:5px;color:{L['navy']}}}
.brand .nm small{{display:block;font-weight:700;font-size:16px;letter-spacing:10px;color:{L['gold']};margin-top:8px;margin-right:-10px}}
.datebox{{display:flex;align-items:center;gap:16px;color:{L['navy']}}}
.datebox .ic{{font-size:54px;color:{L['navy']}}}
.datebox .dl{{border-left:3px solid {L['navy']};padding-left:16px;font-size:25px;line-height:1.45;font-weight:500}}
.datebox .dl b{{font-weight:700}}
/* titles */
.t-tr{{font-weight:900;color:{L['navy']};line-height:1.08;letter-spacing:-.5px}}
.t-en{{font-weight:700;color:{L['navy']};line-height:1.2}}
.t-fa{{font-weight:800;color:{L['navy']};direction:rtl;line-height:1.5}}
.rule{{height:4px;width:200px;background:{L['navy']};border-radius:2px;margin:18px auto 0;opacity:.85}}
.hero{{position:relative;margin:24px -52px 0;height:310px;background-size:cover;background-position:center;
  -webkit-mask-image:linear-gradient(180deg,transparent 0,#000 14%,#000 80%,transparent 100%)}}
.cards{{display:flex;flex-direction:column;gap:18px;flex:1;min-height:0;overflow:hidden}}
.card{{background:{L['card']};border-radius:28px;box-shadow:0 8px 24px rgba(14,47,110,.13),inset 0 0 0 1.5px rgba(255,255,255,.9)}}
/* weather rows */
.wrow{{direction:ltr;display:grid;grid-template-columns:50px 1fr 112px 196px 232px;align-items:center;column-gap:8px;
  padding:10px 26px;height:134px;flex:0 0 auto}}
.wrow .pin{{font-size:46px;color:{L['navy']}}}
.wrow .cn b{{display:block;font-size:40px;font-weight:700;color:{L['navy']};line-height:1.1}}
.wrow .cn span{{font-size:23px;color:{L['muted']};white-space:nowrap}}
.wx{{width:100px;height:100px}}
.wrow .tp{{font-size:68px;white-space:nowrap;font-weight:700;color:{L['navy']};border-left:2px solid #C9D6E6;padding-left:26px;line-height:1}}
.wrow .cd{{border-left:2px solid #C9D6E6;padding-left:22px;font-size:26px;color:{L['ink']};line-height:1.35}}
.wrow .cd i{{font-style:normal;color:{L['muted']};font-size:24px;display:block}}
.wrow .cd .rtl{{display:block;font-weight:700;color:{L['navy']};text-align:left}}
/* news */
.newsbrand{{direction:ltr;display:flex;align-items:center;gap:18px;margin-top:6px}}
.mega{{width:150px;height:150px}}
.nt{{line-height:.95}}
.nt .n1{{display:inline-block;background:linear-gradient(180deg,#F44336,#C62828);color:#fff;font-weight:900;font-style:italic;
  font-size:86px;padding:6px 26px 10px;border-radius:14px;transform:skew(-8deg) rotate(-3deg)}}
.nt .n2{{display:inline-block;background:linear-gradient(180deg,#1E6FE0,#0E3C9A);color:#fff;font-weight:900;font-style:italic;
  font-size:86px;padding:6px 26px 10px;border-radius:14px;transform:skew(-8deg) rotate(-3deg);margin:-6px 0 0 70px}}
.nt .n3{{display:block;color:{L['navy']};font-weight:500;letter-spacing:10px;font-size:26px;margin:14px 0 0 40px}}
.tab{{align-self:flex-start;direction:ltr;margin:-34px 0 0 0;position:relative;z-index:2;display:flex;align-items:center;gap:14px;
  background:linear-gradient(90deg,#E53935,#F0544F);color:#fff;font-weight:900;font-size:36px;
  padding:12px 60px 12px 34px;clip-path:polygon(0 0,88% 0,100% 100%,0 100%);border-radius:18px 0 0 0}}
.tab .ic{{font-size:42px}}
.ncard{{display:flex;gap:28px;align-items:flex-start;padding:30px 34px}}
.ncard .ico{{flex:0 0 auto;width:118px;height:118px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 10px rgba(0,0,0,.18)}}
.ncard .ico svg{{width:100%;height:100%}}
.ncard .ico.topic{{background:radial-gradient(circle at 35% 30%,#2A7BE8,#0E3C9A)}}
.ncard .ico.topic svg{{width:62%;height:62%}}
.ncard .tx{{flex:1;border-left:4px solid {L['navy']};padding-left:26px;min-width:0}}
.ncard.fa .tx{{border-left:0;border-right:4px solid {L['navy']};padding-left:0;padding-right:26px}}
.ncard h2{{font-size:1.55em;font-weight:800;color:{L['navy']};line-height:1.22}}
.ncard.fa h2{{line-height:1.5}}
.ncard p{{font-size:1em;line-height:1.55;color:{L['ink']};margin-top:.4em}}
.ncard.fa p{{line-height:1.85}}
.ncard.ltr{{direction:ltr}} .ncard.fa{{direction:rtl}}
/* pharmacy */
.phead{{position:relative;display:flex;direction:ltr;align-items:center;gap:26px;margin-top:6px;
  background:rgba(255,255,255,.82);border-radius:30px;padding:16px 28px;box-shadow:0 8px 24px rgba(14,47,110,.12)}}
.mortar{{width:130px;height:130px;flex:0 0 auto}}
.phead .tt{{flex:1}}
.phead .tt div{{border-bottom:2px solid {L['navy']};padding:3px 0 6px}}
.phead .tt div:last-child{{border-bottom:0}}
.phead h1{{font-size:46px;font-weight:900;color:{L['navy']};line-height:1.1}}
.phead h1.fa{{direction:rtl;text-align:right;font-size:44px;line-height:1.35}}
.phead small{{font-size:24px;color:{L['ink']};font-weight:500}}
.phead small.fa{{display:block;direction:rtl;text-align:right}}
.regbar{{direction:ltr;align-self:center;margin:18px 0 10px;display:flex;align-items:center;gap:16px;background:linear-gradient(90deg,#1E5BD8,#0E3C9A);
  color:#fff;font-weight:700;font-size:30px;padding:14px 40px;border-radius:50px;box-shadow:0 6px 16px rgba(14,60,154,.3)}}
.regbar .ic{{font-size:40px}}
.prow{{direction:ltr;display:grid;grid-template-columns:170px minmax(0,1fr) max-content;align-items:center;gap:20px;padding:12px 22px 12px 12px;height:128px;position:relative;flex:0 0 auto}}
.prow .th{{width:170px;height:110px;border-radius:18px;background-size:cover;background-position:center;
  box-shadow:0 3px 8px rgba(0,0,0,.15);display:flex;align-items:center;justify-content:center;color:#fff;font-size:60px}}
.prow .pill{{position:absolute;top:-14px;left:164px;display:flex;align-items:center;gap:8px;color:#fff;font-weight:700;font-size:25px;
  padding:5px 22px 6px 14px;border-radius:30px;box-shadow:0 3px 8px rgba(0,0,0,.18)}}
.prow .pill .ic{{font-size:28px}}
.prow .pill .fa{{font-weight:500;opacity:.95;direction:rtl;unicode-bidi:isolate}}
.prow .nm{{padding-top:18px;min-width:0}}
.prow .nm b{{display:block;font-size:35px;font-weight:800;color:{L['navy']};line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.prow .nm span{{display:flex;align-items:center;gap:8px;font-size:23px;color:{L['ink']};margin-top:6px;white-space:nowrap;overflow:hidden}}
.prow .nm span .ic{{font-size:28px;color:{L['navy']}}}
.prow .ph{{border-left:2px solid #C9D6E6;padding-left:22px;display:flex;align-items:center;gap:10px;font-size:26px;font-weight:600;color:{L['navy']};white-space:nowrap}}
.prow .ph .ic{{font-size:36px}}
.feats{{direction:rtl;display:flex;justify-content:center;gap:0;margin-top:12px}}
.feats div{{text-align:center;padding:0 34px;font-size:22px;color:{L['navy']};font-weight:600;line-height:1.35}}
.feats div+div{{border-right:2px solid #BFCDE0}}
.feats svg{{display:block;margin:0 auto 6px;width:54px;height:54px}}
/* footer CTA */
.cta{{direction:rtl;margin-top:22px;display:flex;align-items:center;gap:22px;background:linear-gradient(90deg,#0E3C9A,#1E6FE0);
  border-radius:60px;padding:16px 18px 16px 18px;color:#fff;box-shadow:0 10px 24px rgba(14,60,154,.35)}}
.tg-ic{{width:96px;height:96px;border-radius:50%;background:{L['tg']};display:flex;align-items:center;justify-content:center;
  box-shadow:inset 0 0 0 5px rgba(255,255,255,.35)}}
.tg-ic .ic{{font-size:52px;margin-left:-4px}}
.cta .ct{{flex:1;line-height:1.35}}
.cta .ct b{{display:block;font-size:34px;font-weight:800}}
.cta .ct span{{font-size:24px;opacity:.9}}
.cta .join{{direction:ltr;background:#fff;color:{L['navy']};font-weight:800;font-size:28px;border-radius:40px;padding:16px 30px;
  display:flex;align-items:center;gap:10px}}
.cta .join .ic{{font-size:32px;color:{L['tg']}}}
.foot2{{direction:ltr;display:flex;justify-content:space-between;align-items:center;margin-top:16px;font-size:24px;color:{L['navy']};font-weight:600}}
.foot2 .src{{direction:rtl;color:{L['muted']};font-weight:500}}
"""


def brand_html(logo_uri):
    img = f'<img src="{logo_uri}">' if logo_uri else ""
    return f'<div class="brand">{img}<div class="nm"><b>GHEBRES</b><small>OFFICIAL</small></div></div>'


def datebox(spec):
    tr, en, fa = dates(spec)
    lines = []
    if tr:
        lines.append(f"<div><b>{e(tr)}</b></div>")
    if en:
        lines.append(f"<div>{e(en)}</div>")
    if fa:
        lines.append(f'<div class="rtl" style="text-align:left">{e(fa)}</div>')
    if not lines:
        return "<div></div>"
    return f'<div class="datebox">{CAL}<div class="dl">{"".join(lines)}</div></div>'


def cta(spec):
    src = spec.get("source")
    src_html = f'<span class="src">منبع: {e(src)}</span>' if src else "<span></span>"
    return (f'<div class="cta">{TG}<div class="ct"><b>{e(spec.get("cta_title", "اخبار کامل در کانال تلگرام ما"))}</b>'
            f'<span>{e(spec.get("cta_sub", "اخبار · اطلاعیه‌ها · قبرس شمالی"))}</span></div>'
            f'<div class="join">{svg(TG_PLANE, "-1 -1 26 26")}<span>عضو شوید</span></div></div>'
            f'<div class="foot2"><span>@ghebres_official</span>{src_html}<span>t.me/ghebres_official</span></div>')


FIT_JS = """
<script>
function fitFont(el, min){
  let fs=parseFloat(getComputedStyle(el).fontSize);
  while(fs>min && el.scrollHeight>el.clientHeight+1){fs-=1; el.style.fontSize=fs+'px';}
}
document.fonts.ready.then(()=>{
  document.querySelectorAll('[data-fit]').forEach(el=>fitFont(el, parseFloat(el.dataset.fit)));
  document.body.setAttribute('data-ready','1');
});
</script>"""


def shell(font_face, inner, hero_uri=None):
    return (f'<!doctype html><html lang="fa"><head><meta charset="utf-8"><style>{css(font_face)}</style></head>'
            f'<body><div class="cloud-bg"></div><div class="page">{inner}</div>{FIT_JS}</body></html>')


def hero_div(uri, h=310):
    if not uri:
        return ""
    return f'<div class="hero" style="height:{h}px;background-image:url({uri})"></div>'


# ---------------------------------------------------------------- layouts
def make(ctx):
    """ctx provides font_face(), img(path), logo_uri"""
    ff = ctx["font_face"]
    img = ctx["img"]

    def hero_for(spec, default):
        p = spec.get("image") or str(PHOTOS / default)
        return img(p)

    def weather(spec, fmt):
        rows = spec.get("items", [])
        cap = int(spec.get("per_page") or 6)
        pages = max(1, math.ceil(len(rows) / cap))
        docs = []
        for pi in range(pages):
            out = []
            for it in rows[pi * cap:(pi + 1) * cap]:
                _, c = city(it.get("city"))
                kind = it.get("condition", "sunny")
                en, tr, fa = CONDITIONS.get(kind, (kind, "", ""))
                en, tr, fa = it.get("text_en", en), it.get("text_tr", tr), it.get("text_fa", fa)
                t = it.get("temp", "")
                lo = it.get("low")
                tstr = f"{t}°" if lo is None else f"{t}°"
                out.append(
                    f'<div class="card wrow"><div class="pin">{PIN}</div>'
                    f'<div class="cn"><b>{e(c["tr"])}</b><span>{e(c["en"])} · <span class="rtl">{e(c["fa"])}</span></span></div>'
                    f'{weather_icon(kind)}<div class="tp">{e(tstr)}<span style="font-size:.55em">C</span></div>'
                    f'<div class="cd">{e(tr)}<i>{e(en)}</i><span class="rtl">{e(fa)}</span></div></div>')
            inner = (f'<div class="topbar">{brand_html(ctx["logo_uri"])}{datebox(spec)}</div>'
                     f'<div style="text-align:center;margin-top:18px">'
                     f'<div class="t-tr" style="font-size:70px;white-space:nowrap">{e(spec.get("title_tr", "Kuzey Kıbrıs’ta Hava Durumu"))}</div>'
                     f'<div class="t-en" style="font-size:44px;margin-top:10px">{e(spec.get("title_en", "Weather in Northern Cyprus"))}</div>'
                     f'<div class="t-fa" style="font-size:48px;margin-top:2px">{e(spec.get("title_fa", "وضعیت آب و هوای قبرس شمالی"))}</div>'
                     f'<div class="rule"></div></div>'
                     f'{hero_div(hero_for(spec, "hero-harbor-1.jpg"), 270)}'
                     f'<div class="cards" style="margin-top:-40px;position:relative;gap:16px">{"".join(out)}</div>'
                     f'{cta(spec)}')
            docs.append(shell(ff, inner))
        return docs

    def news3(spec, fmt):
        tr = spec.get("tr", {})
        en = spec.get("en", {})
        fa_ = spec.get("fa", {})
        topic = TOPIC.get(spec.get("icon", "news"), TOPIC["news"])
        cards = []
        if tr:
            ico = (f'<div class="ico">{TR_FLAG}</div>' if spec.get("icon") == "flag"
                   else f'<div class="ico topic">{svg(topic, cls="", fill="#fff")}</div>')
            cards.append(f'<div class="card ncard ltr">{ico}<div class="tx"><h2>{e(tr.get("title"))}</h2><p>{e(tr.get("body"))}</p></div></div>')
        if en:
            cards.append(f'<div class="card ncard ltr"><div class="ico">{UK_FLAG}</div><div class="tx"><h2>{e(en.get("title"))}</h2><p>{e(en.get("body"))}</p></div></div>')
        if fa_:
            cards.append(f'<div class="card ncard fa"><div class="ico">{IR_FLAG}</div><div class="tx"><h2>{e(fa_num(fa_.get("title","")))}</h2><p>{e(fa_num(fa_.get("body","")))}</p></div></div>')
        tab = spec.get("tab", "GÜNÜN HABERİ")
        mega = ('<svg class="mega" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M20 50h18l44-26v72L38 70H20z" fill="#fff" stroke="#0E3C9A" stroke-width="5" stroke-linejoin="round"/>'
                '<path d="M82 24c10 8 15 22 15 36s-5 28-15 36" fill="none" stroke="#E53935" stroke-width="7" stroke-linecap="round"/>'
                '<rect x="12" y="48" width="14" height="24" rx="5" fill="#E53935"/>'
                '<path d="M40 72l8 26h12l-6-24" fill="#0E3C9A"/>'
                '<path d="M104 30l10-8M106 60h12M104 90l10 8" stroke="#E53935" stroke-width="5" stroke-linecap="round"/></svg>')
        inner = (f'<div class="topbar">{brand_html(ctx["logo_uri"])}{datebox(spec)}</div>'
                 f'<div class="newsbrand">{mega}<div class="nt"><span class="n1">NEWS</span><br>'
                 f'<span class="n2">TODAY</span><span class="n3">NORTH CYPRUS · قبرس شمالی</span></div></div>'
                 f'{hero_div(hero_for(spec, "hero-harbor-2.jpg"), 330)}'
                 f'<div class="tab">{svg(TOPIC["news"])}<span>{e(tab)}</span></div>'
                 f'<div class="cards" data-fit="22" style="font-size:33px;gap:22px">{"".join(cards)}</div>'
                 f'{cta(spec)}')
        return [shell(ff, inner)]

    def pharmacy(spec, fmt):
        items = spec.get("items", [])
        cap = int(spec.get("per_page") or 6)
        pages = max(1, math.ceil(len(items) / cap))
        tr, en, fa = dates(spec)
        docs = []
        for pi in range(pages):
            rows = []
            for it in items[pi * cap:(pi + 1) * cap]:
                key, c = city(it.get("city"))
                th = img(it.get("photo") or (str(PHOTOS / f"city-{key}.jpg") if key else None))
                th_html = (f'<div class="th" style="background-image:url({th})"></div>' if th
                           else f'<div class="th" style="background:{c["color"]}">{PIN}</div>')
                rows.append(
                    f'<div class="card prow">{th_html}'
                    f'<div class="pill" style="background:{c["color"]}">{PIN}<span>{e(c["tr"])}</span><span>·</span><span style="font-weight:500">{e(c["en"])}</span><span>·</span>'
                    f'<span class="fa">{e(c["fa"])}</span></div>'
                    f'<div class="nm"><b>{e(it.get("name"))}</b><span>{PIN}{e(it.get("address", ""))}</span></div>'
                    f'<div class="ph">{PHONE}<span>{e(it.get("phone", ""))}</span></div></div>')
            pg = f" · {fa_num(pi+1)}/{fa_num(pages)}" if pages > 1 else ""
            region = spec.get("region")
            if region:
                _, rc = city(region)
                reg = f'{e(rc["tr"])} / {e(rc["en"])} / <span class="rtl">{e(rc["fa"])}</span>'
            else:
                reg = 'Kuzey Kıbrıs / Northern Cyprus / <span class="rtl">قبرس شمالی</span>'
            feats = (
                '<div class="feats">'
                f'<div><svg viewBox="0 0 24 24" fill="none" stroke="{L["navy"]}" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>خدمات اضطراری<br>۲۴ ساعته</div>'
                f'<div><svg viewBox="0 0 24 24" fill="{L["navy"]}"><path d="M12 2C8 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3-7-7-7zm0 9.6A2.6 2.6 0 1 1 12 6.4a2.6 2.6 0 0 1 0 5.2z"/></svg>همه مناطق<br>قبرس شمالی</div>'
                f'<div><svg viewBox="0 0 24 24" fill="{L["navy"]}"><path d="M12 21s-8-5.3-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.7-8 11-8 11z"/></svg>سلامتی شما<br>اولویت ماست</div>'
                '</div>')
            inner = (f'<div class="topbar">{brand_html(ctx["logo_uri"])}<div></div></div>'
                     f'<div class="phead">{MORTAR}<div class="tt">'
                     f'<div><h1>Nöbetçi Eczaneler</h1><small>{e(tr or "")}</small></div>'
                     f'<div><h1>On Duty Pharmacies</h1><small>{e(en or "")}</small></div>'
                     f'<div><h1 class="fa">داروخانه‌های کشیک{e(pg)}</h1><small class="fa">{e(fa or "")}</small></div>'
                     f'</div></div>'
                     f'<div class="regbar">{PIN}<span>{reg}</span></div>'
                     f'<div class="cards" style="gap:24px;padding-top:16px;overflow:visible">{"".join(rows)}</div>'
                     f'{feats}{cta(spec)}')
            docs.append(shell(ff, inner))
        return docs

    return {"weather_classic": weather, "weather_map": make_weather2(ctx, css), "weather": make_weather3(ctx, css), "news3": news3, "pharmacy_classic": pharmacy,
            "pharmacy": make_night(ctx, css)}


# ---------------------------------------------------------------- night pharmacy (creative)
NIGHT_CSS = """
body.night{background:#EEF3F9}
.nsky{position:absolute;left:0;right:0;top:0;height:760px;overflow:hidden;
  background:linear-gradient(180deg,#071433 0%,#0F2557 30%,#2C4C8E 55%,#C98AA0 82%,#F6C9A4 100%)}
.nsky .ph{position:absolute;left:0;right:0;bottom:0;height:330px;background-size:cover;background-position:center 60%;
  filter:saturate(.75) brightness(.62) hue-rotate(-12deg);
  -webkit-mask-image:linear-gradient(180deg,transparent 0,#000 35%,#000 78%,transparent 100%)}
.nsky .glowline{position:absolute;left:0;right:0;bottom:0;height:200px;background:linear-gradient(180deg,transparent,#EEF3F9)}
.star{position:absolute;border-radius:50%;background:#fff}
.moon{position:absolute;top:44px;left:70px;width:96px;height:96px;border-radius:50%;
  background:radial-gradient(circle at 38% 35%,#FFFBEA,#F3E2A8 60%,#D9C27A);box-shadow:0 0 60px 18px rgba(255,236,170,.35)}
.moon:after{content:"";position:absolute;width:96px;height:96px;border-radius:50%;left:28px;top:-14px;background:#0F2557}
.night .brand .nm b{color:#fff}
.night .brand .nm small{color:#F1CE6B}
.sign{position:relative;margin-top:26px;display:flex;direction:ltr;align-items:center;gap:30px;
  background:rgba(6,16,42,.62);border:2px solid rgba(120,255,190,.35);border-radius:34px;padding:26px 34px;
  box-shadow:0 0 0 6px rgba(120,255,190,.06),0 20px 50px rgba(0,0,0,.35);backdrop-filter:blur(6px)}
.cross{flex:0 0 auto;width:150px;height:150px;position:relative}
.cross:before,.cross:after{content:"";position:absolute;background:#34F29A;border-radius:14px;
  box-shadow:0 0 18px #34F29A,0 0 46px rgba(52,242,154,.8),inset 0 0 10px rgba(255,255,255,.6)}
.cross:before{left:50px;top:4px;width:50px;height:142px}
.cross:after{left:4px;top:50px;width:142px;height:50px}
.sign .st{flex:1;color:#fff}
.sign .st .a{font-size:58px;font-weight:900;line-height:1.05;text-shadow:0 0 18px rgba(52,242,154,.55)}
.sign .st .b{font-size:40px;font-weight:700;color:#D7FFEA;margin-top:6px}
.sign .st .c{font-size:46px;font-weight:800;direction:rtl;text-align:left;margin-top:2px;color:#fff}
.dates{direction:ltr;margin-top:18px;display:flex;justify-content:center;gap:14px;flex-wrap:wrap}
.dates span{background:rgba(255,255,255,.92);color:#0E2F6E;font-weight:700;font-size:24px;padding:8px 20px;border-radius:30px;
  box-shadow:0 4px 12px rgba(0,0,0,.15)}
.dates span.fa{direction:rtl}
.groups{position:relative;margin-top:24px;display:flex;flex-direction:column;gap:16px;flex:1;min-height:0}
.grp{background:#fff;border-radius:28px;box-shadow:0 8px 22px rgba(14,47,110,.12);overflow:hidden;position:relative}
.grp .gh{direction:ltr;display:flex;align-items:center;gap:16px;padding:8px 20px;color:#fff}
.grp .gh .av{width:58px;height:58px;border-radius:50%;background-size:cover;background-position:center;border:4px solid rgba(255,255,255,.85);flex:0 0 auto}
.grp .gh b{font-size:34px;font-weight:900}
.grp .gh i{font-style:normal;font-size:26px;opacity:.92;font-weight:500}
.grp .gh .fa{direction:rtl;unicode-bidi:isolate;font-size:30px;font-weight:700}
.grp .gh .cnt{margin-left:auto;background:rgba(255,255,255,.22);border:2px solid rgba(255,255,255,.55);border-radius:30px;
  padding:4px 16px;font-size:24px;font-weight:700;white-space:nowrap}
.ent{direction:ltr;display:grid;grid-template-columns:minmax(0,1fr) max-content;align-items:center;gap:2px 18px;padding:7px 24px 7px 30px;position:relative}
.ent+.ent{border-top:2px dashed #DCE5F0}
.ent .n{font-size:29px;font-weight:800;color:#0E2F6E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ent .ad{grid-column:1;font-size:21px;color:#4A5A75;display:flex;gap:8px;align-items:center;white-space:nowrap;overflow:hidden}
.ent .ad .ic{font-size:24px;color:#0E2F6E}
.ent .tel{grid-column:2;grid-row:1;direction:ltr;display:flex;align-items:center;gap:10px;background:#E7FBF1;color:#0B7A47;
  border:2px solid #8EE6BC;border-radius:30px;padding:3px 16px;font-size:26px;font-weight:800;white-space:nowrap}
.ent .tel .ic{font-size:28px}
.ent .hr{grid-column:2;grid-row:2;justify-self:end;display:flex;align-items:center;gap:8px;font-size:22px;color:#0E2F6E;font-weight:700}
.ent .hr svg{width:24px;height:24px}
.ent:before{content:"";position:absolute;left:12px;top:22px;width:8px;height:8px;border-radius:50%;background:var(--c)}
.emgb{flex:0 0 auto;align-self:stretch;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;
  background:#E53935;color:#fff;border-radius:22px;padding:10px 18px;font-size:17px;font-weight:700;letter-spacing:1px;box-shadow:0 0 22px rgba(229,57,53,.55)}
.emgb b{font-size:50px;font-weight:900;letter-spacing:0;line-height:1}
.emgb .rtl{font-size:19px;letter-spacing:0}
.emg{direction:ltr;margin-top:18px;display:flex;align-items:center;justify-content:center;gap:16px;font-size:26px;font-weight:700;color:#0E2F6E}
.emg b{background:#E53935;color:#fff;border-radius:14px;padding:4px 16px;font-size:30px}
"""

CLOCK = ('<svg viewBox="0 0 24 24" fill="none" stroke="#0E2F6E" stroke-width="2.2">'
         '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2" stroke-linecap="round"/></svg>')


def make_night(ctx, base_css_fn):
    img = ctx["img"]
    ff = ctx["font_face"]
    stars = "".join(
        f'<div class="star" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;opacity:{o}"></div>'
        for x, y, s, o in [(260, 60, 3, .9), (420, 110, 2, .7), (600, 70, 3, .8), (760, 140, 2, .6), (980, 210, 3, .8),
                           (340, 230, 2, .6), (880, 60, 2, .7), (150, 330, 2, .5), (700, 260, 2, .5), (520, 30, 2, .6),
                           (1020, 330, 2, .5), (60, 90, 2, .6)])

    def group_html(key, c, ents, total, cont=False):
        th = img(str(PHOTOS / f"city-{key}.jpg")) if key else None
        av = f'<div class="av" style="background-image:url({th})"></div>' if th else ""
        cnt = f'{len(ents) if not cont else ""}'
        rows = []
        for it in ents:
            hrs = it.get("hours")
            hr = f'<div class="hr">{CLOCK}<span>{e(hrs)}</span></div>' if hrs else ""
            rows.append(
                f'<div class="ent" style="--c:{c["color"]}"><div class="n">{e(it.get("name"))}</div>'
                f'<div class="tel">{PHONE}<span>{e(it.get("phone", ""))}</span></div>'
                f'<div class="ad">{PIN}<span>{e(it.get("address", ""))}</span></div>{hr}</div>')
        label = f"{total} eczane · {total} pharmacies" if not cont else "devam · continued"
        return (f'<div class="grp"><div class="gh" style="background:linear-gradient(90deg,{c["color"]},{c["color"]}CC)">{av}'
                f'<b>{e(c["tr"])}</b><i>{e(c["en"])}</i><span class="fa">{e(c["fa"])}</span>'
                f'<span class="cnt">{e(label)}</span></div>{"".join(rows)}</div>')

    def pharmacy(spec, fmt):
        tr, en, fa = dates(spec)
        # group by city, in a fixed geographic order
        order = list(CITIES.keys())
        groups = {}
        for it in spec.get("items", []):
            key, c = city(it.get("city"))
            groups.setdefault(key or it.get("city"), (key, c, []))[2].append(it)
        seq = sorted(groups.values(), key=lambda g: order.index(g[0]) if g[0] in order else 99)
        # paginate by estimated height
        budget = int(spec.get("page_budget", 1150))
        H_HEAD, H_ENT, H_GAP = 74, 100, 16

        def paginate(budget):
            pages, cur, used = [], [], 0
            for key, c, ents in seq:
                need = H_HEAD + H_ENT * len(ents) + (H_GAP if cur else 0)
                if cur and used + need > budget and H_HEAD + H_ENT * len(ents) <= budget:
                    pages.append(cur)
                    cur, used = [], 0
                i = 0
                while i < len(ents):
                    room = budget - used - H_HEAD - (H_GAP if cur else 0)
                    fit_n = max(0, room // H_ENT)
                    if fit_n == 0:
                        pages.append(cur)
                        cur, used = [], 0
                        continue
                    part = ents[i:i + fit_n]
                    cur.append((key, c, part, len(ents), i > 0))
                    used += (H_GAP if len(cur) > 1 else 0) + H_HEAD + H_ENT * len(part)
                    i += len(part)
            if cur:
                pages.append(cur)
            return pages

        pages = paginate(budget)
        if len(pages) > 1:  # balance pages so the last one isn't nearly empty
            total = sum(H_HEAD + H_ENT * len(g[2]) + H_GAP for g in seq)
            lo = max(H_HEAD + H_ENT, total // len(pages))
            for b in range(lo, budget, 20):
                cand = paginate(b)
                if len(cand) == len(pages):
                    pages = cand
                    break
        if not pages:
            pages = [[]]
        docs = []
        hero = img(spec.get("image") or str(PHOTOS / "hero-harbor-2.jpg"))
        emg = spec.get("emergency", "112")
        for pi, pg in enumerate(pages):
            pgl = f'<span style="background:#34F29A;color:#06331E">{pi+1} / {len(pages)}</span>' if len(pages) > 1 else ""
            body = "".join(group_html(*g) for g in pg)
            inner = (f'<div class="topbar">{brand_html(ctx["logo_uri"])}<div></div></div>'
                     f'<div class="sign"><div class="cross"></div><div class="st">'
                     f'<div class="a">Nöbetçi Eczaneler</div><div class="b">On Duty Pharmacies</div>'
                     f'<div class="c">داروخانه‌های کشیک</div></div>'
                     f'<div class="emgb"><span>ACİL</span><b>{e(emg)}</b><span>EMERGENCY</span><span class="rtl">اورژانس</span></div></div>'
                     f'<div class="dates">{f"<span>{e(tr)}</span>" if tr else ""}{f"<span>{e(en)}</span>" if en else ""}'
                     f'{f"<span class=fa>{e(fa)}</span>" if fa else ""}{pgl}</div>'
                     f'<div class="groups">{body}</div>'
                     f'{cta(spec)}')
            html_doc = (f'<!doctype html><html lang="fa"><head><meta charset="utf-8"><style>{base_css_fn(ff)}{NIGHT_CSS}</style></head>'
                        f'<body class="night"><div class="nsky">{stars}<div class="moon"></div>'
                        f'<div class="ph" style="background-image:url({hero})"></div><div class="glowline"></div></div>'
                        f'<div class="page">{inner}</div>{FIT_JS}</body></html>')
            docs.append(html_doc)
        return docs

    return pharmacy


# ---------------------------------------------------------------- creative weather (map + tiles)
COORDS = {"lefkosa": (33.36, 35.18), "girne": (33.32, 35.335), "magusa": (33.94, 35.12),
          "iskele": (33.89, 35.29), "guzelyurt": (32.99, 35.20), "lefke": (32.84, 35.11),
          "karpaz": (34.37, 35.60)}
# rough Cyprus coastline (lon, lat), clockwise from Cape Kormakitis
COAST = [(32.94, 35.39), (33.08, 35.36), (33.20, 35.35), (33.32, 35.345), (33.45, 35.35), (33.60, 35.37),
         (33.75, 35.40), (33.92, 35.44), (34.08, 35.47), (34.22, 35.52), (34.35, 35.57), (34.48, 35.63),
         (34.59, 35.69), (34.55, 35.66), (34.42, 35.56), (34.25, 35.45), (34.10, 35.36), (33.96, 35.28),
         (33.93, 35.20), (33.92, 35.12), (33.98, 35.04), (34.07, 34.98), (33.90, 34.95), (33.64, 34.90),
         (33.60, 34.82), (33.25, 34.70), (33.02, 34.65), (32.92, 34.60), (32.76, 34.65), (32.60, 34.68),
         (32.41, 34.75), (32.32, 34.95), (32.27, 35.07), (32.35, 35.10), (32.42, 35.04), (32.55, 35.17),
         (32.71, 35.18), (32.85, 35.20), (32.92, 35.28)]

W2_CSS = """
body.w2{background:linear-gradient(180deg,var(--s1) 0%,var(--s2) 34%,var(--s3) 70%,#F3F8FC 100%)}
body.w2.sunny{--s1:#4FB3EE;--s2:#A9DBF7;--s3:#EAF6FD}
body.w2.cloudy{--s1:#7F97B2;--s2:#BCCADA;--s3:#E9EEF4}
body.w2.rain{--s1:#3E5B7E;--s2:#8EA6C1;--s3:#E3EAF2}
.sunglow{position:absolute;top:-180px;left:-160px;width:620px;height:620px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,236,150,.95) 0,rgba(255,214,90,.55) 22%,rgba(255,214,90,0) 62%)}
body.w2.cloudy .sunglow,body.w2.rain .sunglow{opacity:.25}
.rainfx{position:absolute;inset:0;opacity:.0;background:repeating-linear-gradient(105deg,rgba(255,255,255,.0) 0 18px,rgba(255,255,255,.35) 18px 20px)}
body.w2.rain .rainfx{opacity:.35;-webkit-mask-image:linear-gradient(180deg,#000,transparent 45%)}
.w2 .ttl{text-align:center;margin-top:8px}
.w2 .ttl .a{font-size:66px;font-weight:900;color:#fff;text-shadow:0 4px 18px rgba(14,47,110,.35);white-space:nowrap}
.w2 .ttl .b{font-size:40px;font-weight:700;color:#0E2F6E;margin-top:2px}
.w2 .ttl .c{font-size:44px;font-weight:800;color:#0E2F6E;direction:rtl}
.w2 .dts{direction:ltr;display:flex;justify-content:center;gap:12px;margin-top:14px}
.w2 .dts span{background:rgba(255,255,255,.85);color:#0E2F6E;font-weight:700;font-size:23px;padding:7px 18px;border-radius:30px}
.w2 .dts .fa{direction:rtl}
.mapcard{position:relative;margin-top:20px;height:540px;border-radius:34px;overflow:hidden;
  background:linear-gradient(160deg,#2C9AD8 0%,#1673B8 60%,#0F5C9C 100%);box-shadow:0 14px 34px rgba(14,47,110,.3)}
.mapcard svg.map{position:absolute;inset:0;width:100%;height:100%}
.bub{position:absolute;transform:translate(-50%,-100%);display:flex;flex-direction:column;align-items:center}
.bub .bx{direction:ltr;display:flex;align-items:center;gap:4px;background:#fff;border-radius:22px;padding:2px 14px 2px 4px;
  box-shadow:0 6px 14px rgba(0,0,0,.25);font-weight:900;font-size:34px;color:#0E2F6E;white-space:nowrap}
.bub .bx .wx{width:56px;height:56px}
.bub .nm{margin-top:4px;font-size:19px;font-weight:800;color:#0E2F6E;background:rgba(255,248,225,.9);border-radius:10px;padding:0 8px}
.pin0{position:absolute;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;background:#E53935;border:3px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.35)}
.bub .dot{width:14px;height:14px;border-radius:50%;background:#E53935;border:3px solid #fff;margin-top:3px;box-shadow:0 2px 4px rgba(0,0,0,.3)}
.maplbl{position:absolute;left:22px;bottom:16px;direction:ltr;color:#fff;font-weight:700;font-size:21px;opacity:.9;letter-spacing:1px}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
.tile{direction:ltr;position:relative;background:rgba(255,255,255,.93);border-radius:26px;padding:18px 18px 18px 22px;
  box-shadow:0 8px 20px rgba(14,47,110,.12);display:grid;grid-template-columns:96px 1fr auto;align-items:center;gap:4px 12px;overflow:hidden}
.tile:before{content:"";position:absolute;left:0;top:0;bottom:0;width:9px;background:var(--c)}
.tile .wx{width:96px;height:96px;grid-row:1 / span 2}
.tile .cn b{display:block;font-size:33px;font-weight:900;color:#0E2F6E;line-height:1.1}
.tile .cn span{font-size:19px;color:#5B6B85;white-space:nowrap}
.tile .tt{text-align:right;line-height:1}
.tile .tt b{font-size:58px;font-weight:900;color:#0E2F6E}
.tile .tt i{display:block;font-style:normal;font-size:22px;color:#5B6B85;font-weight:700;margin-top:4px}
.tile .cd{grid-column:2 / span 2;font-size:18px;color:#1D2B44;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tile .cd .rtl{font-weight:700;color:#0E2F6E}
.hls{direction:ltr;display:flex;gap:14px;margin-top:18px}
.hl{flex:1;border-radius:22px;padding:12px 16px;color:#fff;box-shadow:0 6px 16px rgba(14,47,110,.18);display:flex;flex-direction:column;gap:4px}
.hl .k{font-size:17px;font-weight:600;opacity:.95;white-space:nowrap}
.hl b{font-size:30px;font-weight:900;white-space:nowrap}
.hl.hot{background:linear-gradient(135deg,#FF8A3D,#E5533B)}
.hl.cool{background:linear-gradient(135deg,#3AA5E8,#1E5BD8)}
.hl.sun{background:linear-gradient(135deg,#F6B21B,#E08A0B)}
"""


def make_weather2(ctx, base_css_fn):
    ff = ctx["font_face"]
    LON0, LON1, LAT0, LAT1 = 32.62, 34.70, 34.93, 35.72
    W, H = 976, 540
    NUDGE = {"karpaz": (-110, 92), "girne": (-70, -8), "lefkosa": (40, 22), "iskele": (-20, -4), "magusa": (10, 18), "guzelyurt": (-10, 6)}

    def xy(lon, lat):
        return (lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H

    def island():
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(*p) for p in COAST))
        waves = "".join(
            f'<path d="M{x} {y} q18 -10 36 0 t36 0" stroke="rgba(255,255,255,.25)" stroke-width="3" fill="none"/>'
            for x, y in [(60, 60), (300, 40), (560, 80), (80, 330), (700, 360), (840, 120), (420, 400)])
        return (f'<svg class="map" viewBox="0 0 {W} {H}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
                f'<defs><linearGradient id="isl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F8EBC4"/>'
                f'<stop offset="1" stop-color="#E7CF94"/></linearGradient>'
                f'<filter id="sh" x="-5%" y="-5%" width="110%" height="120%"><feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#06345e" flood-opacity=".45"/></filter></defs>'
                f'{waves}<polygon points="{pts}" fill="url(#isl)" stroke="#fff" stroke-width="5" stroke-linejoin="round" filter="url(#sh)"/>'
                f'<polygon points="{pts}" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="16" stroke-linejoin="round" transform="translate(0 2)"/>'
                f'{ridge()}</svg>')

    def ridge():
        pts = [(32.95, 35.30), (33.10, 35.29), (33.25, 35.30), (33.45, 35.31), (33.65, 35.33), (33.85, 35.37), (34.0, 35.40)]
        tri = ""
        for i, (lon, lat) in enumerate(pts):
            x, y = xy(lon, lat)
            h = 16 + (i % 3) * 6
            tri += f'<path d="M{x-24:.0f} {y+8:.0f} L{x:.0f} {y-h:.0f} L{x+24:.0f} {y+8:.0f}Z" fill="#C9A86A" opacity=".55"/>'
            tri += f'<path d="M{x-6:.0f} {y-h+8:.0f} L{x:.0f} {y-h:.0f} L{x+6:.0f} {y-h+8:.0f}Z" fill="#fff" opacity=".6"/>'
        return tri

    def dominant(items):
        score = {"sunny": 0, "cloudy": 0, "rain": 0}
        for it in items:
            k = it.get("condition", "sunny")
            score["rain" if k in ("rain", "storm") else "cloudy" if k in ("cloudy", "fog") else "sunny"] += 1
        return max(score, key=score.get)

    def highlights(spec, items):
        chips = []
        withT = [it for it in items if isinstance(it.get("temp"), (int, float))]
        if withT:
            hot = max(withT, key=lambda i: i["temp"])
            cool = min(withT, key=lambda i: i.get("low", i["temp"]))
            _, ch = city(hot["city"])
            _, cc = city(cool["city"])
            chips.append(f'<div class="hl hot"><span class="k">En sıcak · Hottest · <span class="rtl">گرم‌ترین</span></span>'
                         f'<b>{e(ch["tr"])} {e(hot["temp"])}°</b></div>')
            cv = cool.get("low", cool["temp"])
            chips.append(f'<div class="hl cool"><span class="k">En serin · Coolest · <span class="rtl">خنک‌ترین</span></span>'
                         f'<b>{e(cc["tr"])} {e(cv)}°</b></div>')
        if spec.get("sunrise") and spec.get("sunset"):
            chips.append(f'<div class="hl sun"><span class="k">Gün doğumu / batımı · <span class="rtl">طلوع / غروب</span></span>'
                         f'<b>☀ {e(spec["sunrise"])} · ☾ {e(spec["sunset"])}</b></div>')
        return f'<div class="hls">{"".join(chips)}</div>' if chips else ""

    def weather(spec, fmt):
        items = spec.get("items", [])[:8]
        tr, en, fa = dates(spec)
        bubbles, tiles = [], []
        for it in items:
            key, c = city(it.get("city"))
            kind = it.get("condition", "sunny")
            ctr, cen, cfa = (lambda t: (t[1], t[0], t[2]))(CONDITIONS.get(kind, (kind, kind, kind)))
            ctr, cen, cfa = it.get("text_tr", ctr), it.get("text_en", cen), it.get("text_fa", cfa)
            t, lo = it.get("temp", ""), it.get("low")
            if key in COORDS:
                x, y = xy(*COORDS[key])
                dx, dy = NUDGE.get(key, (0, 0))
                bubbles.append(f'<div class="pin0" style="left:{x:.0f}px;top:{y:.0f}px"></div>')
                bubbles.append(f'<div class="bub" style="left:{x+dx:.0f}px;top:{y+dy-6:.0f}px"><div class="bx">{weather_icon(kind)}{e(t)}°</div>'
                               f'<div class="nm">{e(c["tr"])}</div></div>')
            low = f'<i>↓ {e(lo)}°</i>' if lo is not None else ""
            tiles.append(f'<div class="tile" style="--c:{c["color"]}">{weather_icon(kind)}'
                         f'<div class="cn"><b>{e(c["tr"])}</b><span>{e(c["en"])} · <span class="rtl">{e(c["fa"])}</span></span></div>'
                         f'<div class="tt"><b>{e(t)}°</b>{low}</div>'
                         f'<div class="cd">{e(ctr)} · {e(cen)} · <span class="rtl">{e(cfa)}</span></div></div>')
        dts = (f'<div class="dts">{f"<span>{e(tr)}</span>" if tr else ""}{f"<span>{e(en)}</span>" if en else ""}'
               f'{f"<span class=fa>{e(fa)}</span>" if fa else ""}</div>')
        inner = (f'<div class="topbar">{brand_html(ctx["logo_uri"])}<div></div></div>'
                 f'<div class="ttl"><div class="a" style="font-size:{min(66, int(66 * 27 / max(1, len(spec.get("title_tr", "Kuzey Kıbrıs’ta Hava Durumu")))))}px">{e(spec.get("title_tr", "Kuzey Kıbrıs’ta Hava Durumu"))}</div>'
                 f'<div class="b">{e(spec.get("title_en", "Weather in Northern Cyprus"))}</div>'
                 f'<div class="c">{e(spec.get("title_fa", "وضعیت آب و هوای قبرس شمالی"))}</div></div>{dts}'
                 f'<div class="mapcard">{island()}{"".join(bubbles)}<div class="maplbl">KUZEY KIBRIS · NORTHERN CYPRUS</div></div>'
                 f'<div class="tiles">{"".join(tiles)}</div>'
                 f'{highlights(spec, items)}'
                 f'<div style="flex:1"></div>{cta(spec)}')
        theme = dominant(items)
        return [(f'<!doctype html><html lang="fa"><head><meta charset="utf-8"><style>{base_css_fn(ff)}{W2_CSS}</style></head>'
                 f'<body class="w2 {theme}"><div class="sunglow"></div><div class="rainfx"></div>'
                 f'<div class="page">{inner}</div>{FIT_JS}</body></html>')]

    return weather


# ---------------------------------------------------------------- Mediterranean weather (sea, flowers, palm, glass rows)
import base64 as _b64
import random as _rnd

FONTS_DIR = ROOT / "assets" / "fonts"


def _script_face():
    p = FONTS_DIR / "DancingScript.ttf"
    if not p.exists():
        return ""
    return ("@font-face{font-family:'Dancing';font-weight:400 700;src:url(data:font/ttf;base64,"
            + _b64.b64encode(p.read_bytes()).decode() + ") format('truetype');}")


def _flowers(cx, cy, n, spread, seed):
    """Bougainvillea cluster: leaves + magenta papery bracts."""
    r = _rnd.Random(seed)
    out = []
    for _ in range(int(n * .7)):
        x, y = cx + r.uniform(-spread, spread), cy + r.uniform(-spread, spread)
        a = r.uniform(0, 360)
        g = r.choice(["#2F7D3A", "#3E9447", "#5BAA4E", "#27652F"])
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r.uniform(16,26):.0f}" ry="{r.uniform(7,11):.0f}" '
                   f'fill="{g}" transform="rotate({a:.0f} {x:.0f} {y:.0f})"/>')
    for _ in range(n):
        x, y = cx + r.uniform(-spread, spread), cy + r.uniform(-spread, spread)
        s = r.uniform(9, 17)
        col = r.choice(["#E8418C", "#F25C9E", "#D62E7A", "#F47AB5", "#C2186B"])
        rot = r.uniform(0, 120)
        petals = "".join(
            f'<ellipse cx="{x:.1f}" cy="{y - s * .55:.1f}" rx="{s * .5:.1f}" ry="{s * .62:.1f}" fill="{col}" '
            f'transform="rotate({rot + k * 120:.0f} {x:.1f} {y:.1f})"/>' for k in range(3))
        out.append(petals + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s * .16:.1f}" fill="#FFF2B3"/>')
    return "".join(out)


def _palm(x, y, h, lean=-14):
    """Stylised palm silhouette: segmented trunk + arched fronds."""
    segs = []
    tx, ty = x, y
    n = 14
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x + lean * t * t * 6, y - h * t))
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        w = 30 - i * 1.1
        segs.append(f'<path d="M{x1 - w / 2:.0f} {y1:.0f} L{x2 - w / 2 + 2:.0f} {y2:.0f} L{x2 + w / 2 - 2:.0f} {y2:.0f} L{x1 + w / 2:.0f} {y1:.0f}Z" '
                    f'fill="{"#7A5A36" if i % 2 else "#8E6B43"}"/>')
    hx, hy = pts[-1]
    fronds = []
    for ang, ln in [(-170, 230), (-140, 260), (-110, 220), (-75, 210), (-40, 250), (-10, 230), (20, 190), (160, 200), (195, 210)]:
        import math as _m
        a = _m.radians(ang)
        ex, ey = hx + _m.cos(a) * ln, hy + _m.sin(a) * ln * .55 + ln * .32
        mx, my = hx + _m.cos(a) * ln * .5, hy + _m.sin(a) * ln * .5 - 40
        fronds.append(f'<path d="M{hx:.0f} {hy:.0f} Q{mx:.0f} {my:.0f} {ex:.0f} {ey:.0f}" stroke="#2E6B34" stroke-width="7" fill="none" stroke-linecap="round"/>')
        for k in range(1, 9):
            t = k / 9
            px = (1 - t) ** 2 * hx + 2 * (1 - t) * t * mx + t * t * ex
            py = (1 - t) ** 2 * hy + 2 * (1 - t) * t * my + t * t * ey
            L = 46 * (1 - t * .55)
            fronds.append(f'<path d="M{px:.0f} {py:.0f} l{L * .55:.0f} {L:.0f}" stroke="#3C8A42" stroke-width="6" stroke-linecap="round"/>'
                          f'<path d="M{px:.0f} {py:.0f} l{-L * .6:.0f} {L * .9:.0f}" stroke="#4FA052" stroke-width="6" stroke-linecap="round"/>')
    coco = "".join(f'<circle cx="{hx + dx}" cy="{hy + dy}" r="13" fill="#6B4A2A"/>' for dx, dy in [(-12, 10), (10, 12), (0, 22)])
    return "".join(segs) + "".join(fronds) + coco


W3_CSS = """
body.w3{background:linear-gradient(180deg,#7FC6F0 0%,#BFE5FA 20%,#E6F5FD 30%,#2D93D3 45%,#1C78BE 70%,#105C9E 100%)}
body.w3.rain{background:linear-gradient(180deg,#6F87A3 0%,#A9BBCF 20%,#DCE4EE 30%,#3F7FB0 45%,#2A6A9E 70%,#1B527F 100%)}
body.w3.cloudy{background:linear-gradient(180deg,#8FB2D0 0%,#C6D8E8 20%,#E8EFF6 30%,#2F8BC8 45%,#1E73B4 70%,#125C98 100%)}
body.w3.rain .sun2,body.w3.cloudy .sun2{opacity:.25}
body.w3.rain .photo{filter:saturate(.7) brightness(.9)}
.w3 .sun2{position:absolute;top:-220px;left:-200px;width:720px;height:720px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,246,200,.95) 0,rgba(255,226,130,.55) 20%,rgba(255,226,130,0) 60%)}
.w3 .cloud1,.w3 .cloud2{position:absolute;border-radius:100px;background:rgba(255,255,255,.75);filter:blur(14px)}
.w3 .cloud1{top:70px;right:-60px;width:420px;height:70px}
.w3 .cloud2{top:180px;left:380px;width:300px;height:50px;opacity:.6}
.w3 .photo{position:absolute;left:0;right:0;top:510px;height:380px;background-size:cover;background-position:center;
  -webkit-mask-image:linear-gradient(180deg,transparent 0,#000 16%,#000 82%,transparent 100%)}
.w3 .seafx{position:absolute;left:0;right:0;top:860px;bottom:0;
  background:repeating-linear-gradient(176deg,rgba(255,255,255,0) 0 26px,rgba(255,255,255,.06) 26px 29px),
             radial-gradient(60% 30% at 70% 10%,rgba(255,255,255,.22),transparent 70%)}
.w3 svg.deco{position:absolute;inset:0;width:1080px;height:1920px;pointer-events:none}
.w3 svg.deco.front{z-index:3}
.w3 .tbox{position:relative;display:flex;direction:ltr;align-items:center;justify-content:center;gap:22px;margin-top:6px}
.w3 .tbox .big{width:190px;height:170px;flex:0 0 auto;filter:drop-shadow(0 8px 14px rgba(14,47,110,.25))}
.w3 .tbox .tt{text-align:center}
.w3 .tbox .big .wx{width:100%;height:100%}
.w3 .tt .a{font-weight:900;color:#0E2F6E;line-height:1.02;letter-spacing:-1px}
.w3 .t2{text-align:center;margin-top:6px}
.w3 .t2 .b{font-size:46px;font-weight:700;color:#0E2F6E}
.w3 .t2 .c{font-size:48px;font-weight:800;color:#0E2F6E;direction:rtl;line-height:1.45}
.w3 .t2 .dl{height:4px;width:190px;background:#0E2F6E;border-radius:2px;margin:12px auto 0;opacity:.8}
.w3 .dts{direction:ltr;display:flex;justify-content:center;gap:12px;margin-top:16px}
.w3 .dts span{background:rgba(255,255,255,.88);color:#0E2F6E;font-weight:700;font-size:23px;padding:7px 18px;border-radius:30px;
  box-shadow:0 3px 10px rgba(14,47,110,.12)}
.w3 .dts .fa{direction:rtl}
.w3 .rows{position:relative;margin-top:auto;display:flex;flex-direction:column;gap:12px;padding:0 6px}
.w3 .row{direction:ltr;display:grid;grid-template-columns:46px minmax(0,1fr) 108px 186px 210px;align-items:center;column-gap:10px;
  height:104px;padding:0 24px;border-radius:24px;background:linear-gradient(180deg,rgba(255,255,255,.86),rgba(235,246,255,.78));
  border:2px solid rgba(255,255,255,.95);box-shadow:0 10px 26px rgba(4,40,90,.28);backdrop-filter:blur(8px)}
.w3 .row .ic{font-size:44px;color:#0E2F6E}
.w3 .row .cn b{display:block;font-size:40px;font-weight:800;color:#0E2F6E;line-height:1.1}
.w3 .row .cn span{font-size:22px;color:#4A5A75;white-space:nowrap}
.w3 .row .wx{width:92px;height:92px}
.w3 .row .tp{border-left:2px solid #C3D3E6;padding-left:22px;line-height:1;white-space:nowrap}
.w3 .row .tp b{font-size:60px;font-weight:900;color:#0E2F6E}
.w3 .row .tp small{font-size:30px;font-weight:800;color:#0E2F6E}
.w3 .row .tp i{display:block;font-style:normal;font-size:22px;color:#4A5A75;font-weight:700;margin-top:4px}
.w3 .row .cd{border-left:2px solid #C3D3E6;padding-left:18px;font-size:24px;line-height:1.3;color:#1D2B44;white-space:nowrap}
.w3 .row .cd i{font-style:normal;display:block;color:#4A5A75;font-size:22px}
.w3 .row .cd .rtl{display:block;text-align:left;font-weight:800;color:#0E2F6E}
.w3 .chips{position:relative;direction:ltr;display:flex;justify-content:center;gap:12px;margin-top:16px}
.w3 .chips>span{background:rgba(6,40,90,.55);border:1.5px solid rgba(255,255,255,.45);color:#fff;font-weight:700;font-size:23px;
  padding:7px 18px;border-radius:30px;backdrop-filter:blur(6px);white-space:nowrap}
.w3 .chips .rtl{direction:rtl}
.w3 .slogan{position:relative;direction:ltr;text-align:center;margin-top:12px;color:#fff;text-shadow:0 3px 10px rgba(0,0,0,.35);line-height:1}
.w3 .slogan b{font-family:'Dancing',cursive;font-weight:700;font-size:56px}
.w3 .slogan i{display:block;font-style:normal;font-family:'Dancing',cursive;font-size:32px;margin-top:2px;opacity:.95}
.w3 .cta{margin-top:16px}
.w3 .foot2{color:#fff}.w3 .foot2 .src{color:#DDEBFA}
"""


def make_weather3(ctx, base_css_fn):
    ff = ctx["font_face"]
    img = ctx["img"]

    def big_icon():
        return ('<svg class="big" viewBox="0 0 190 170" xmlns="http://www.w3.org/2000/svg"><defs>'
                '<radialGradient id="bs" cx="40%" cy="35%"><stop offset="0" stop-color="#FFE98A"/><stop offset="1" stop-color="#F4A30C"/></radialGradient>'
                '<linearGradient id="bc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#C9D6E4"/></linearGradient></defs>'
                + "".join(f'<rect x="76" y="6" width="9" height="26" rx="4.5" fill="#F6B21B" transform="rotate({a} 80 72)"/>' for a in range(-90, 181, 45))
                + '<circle cx="80" cy="72" r="44" fill="url(#bs)"/>'
                  '<g fill="url(#bc)"><circle cx="104" cy="122" r="30"/><circle cx="138" cy="108" r="36"/><circle cx="166" cy="128" r="22"/>'
                  '<rect x="78" y="122" width="108" height="34" rx="17"/></g></svg>')

    def deco():
        back = (_flowers(30, 640, 30, 55, 4) + _flowers(10, 790, 36, 60, 5) + _flowers(1060, 590, 22, 45, 6))
        front = (_flowers(-6, 1560, 34, 48, 1) + _flowers(-10, 1700, 30, 44, 2) + _flowers(18, 1640, 18, 30, 3))
        return (f'<svg class="deco" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">'
                f'<g>{back}</g></svg>',
                f'<svg class="deco front" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg"><g>{front}</g></svg>')

    def weather(spec, fmt):
        items = spec.get("items", [])[:6]
        tr, en, fa = dates(spec)
        rows = []
        for it in items:
            _, c = city(it.get("city"))
            kind = it.get("condition", "sunny")
            cen, ctr, cfa = CONDITIONS.get(kind, (kind, kind, kind))
            ctr, cen, cfa = it.get("text_tr", ctr), it.get("text_en", cen), it.get("text_fa", cfa)
            lo = it.get("low")
            low = f'<i>↓ {e(lo)}°</i>' if lo is not None else ""
            rows.append(f'<div class="row"><div>{PIN}</div>'
                        f'<div class="cn"><b>{e(c["tr"])}</b><span>{e(c["en"])} · <span class="rtl">{e(c["fa"])}</span></span></div>'
                        f'{weather_icon(kind)}<div class="tp"><b>{e(it.get("temp", ""))}</b><small>°C</small>{low}</div>'
                        f'<div class="cd">{e(ctr)}<i>{e(cen)}</i><span class="rtl">{e(cfa)}</span></div></div>')
        score = {"sunny": 0, "cloudy": 0, "rain": 0}
        for it in items:
            k = it.get("condition", "sunny")
            score["rain" if k in ("rain", "storm") else "cloudy" if k in ("cloudy", "fog") else "sunny"] += 1
        theme = max(score, key=score.get)
        title = spec.get("title_tr", "Kuzey Kıbrıs’ta Hava Durumu")
        # split Turkish title over two lines like a poster headline
        words = title.split()
        cut = max(1, len(words) // 2)
        l1, l2 = " ".join(words[:cut]), " ".join(words[cut:])
        tsize = min(86, int(86 * 16 / max(len(l1), len(l2), 1)))
        chips = []
        withT = [i for i in items if isinstance(i.get("temp"), (int, float))]
        if withT:
            hot = max(withT, key=lambda i: i["temp"])
            _, ch = city(hot["city"])
            chips.append(f'<span>🌡 En sıcak · Hottest · <span class="rtl">گرم‌ترین</span>: {e(ch["tr"])} {e(hot["temp"])}°</span>')
        if spec.get("sunrise"):
            chips.append(f'<span>☀ {e(spec["sunrise"])} · ☾ {e(spec["sunset"])}</span>')
        dts = (f'<div class="dts">{f"<span>{e(tr)}</span>" if tr else ""}{f"<span>{e(en)}</span>" if en else ""}'
               f'{f"<span class=fa>{e(fa)}</span>" if fa else ""}</div>')
        inner = (f'<div class="topbar">{brand_html(ctx["logo_uri"])}<div></div></div>'
                 f'<div class="tbox">{big_icon() if theme == "sunny" else ("<div class=big>" + weather_icon("rain" if theme == "rain" else "cloudy") + "</div>")}<div class="tt"><div class="a" style="font-size:{tsize}px">{e(l1)}<br>{e(l2)}</div></div></div>'
                 f'<div class="t2"><div class="b">{e(spec.get("title_en", "Weather in Northern Cyprus"))}</div>'
                 f'<div class="c">{e(spec.get("title_fa", "وضعیت آب و هوای قبرس شمالی"))}</div><div class="dl"></div></div>{dts}'
                 f'<div class="rows">{"".join(rows)}</div>'
                 f'<div class="chips">{"".join(chips)}</div>'
                 f'<div class="slogan"><b>Northern Cyprus</b><i>a beautiful day by the sea</i></div>'
                 f'{cta(spec)}')
        photo = img(spec.get("image") or str(PHOTOS / "hero-harbor-1.jpg"))
        dk = deco()
        return [(f'<!doctype html><html lang="fa"><head><meta charset="utf-8"><style>{base_css_fn(ff)}{_script_face()}{W3_CSS}</style></head>'
                 f'<body class="w3 {theme}"><div class="sun2"></div><div class="cloud1"></div><div class="cloud2"></div>'
                 f'<div class="photo" style="background-image:url({photo})"></div><div class="seafx"></div>{dk[0]}'
                 f'<div class="page">{inner}</div>{dk[1]}{FIT_JS}</body></html>')]

    return weather
