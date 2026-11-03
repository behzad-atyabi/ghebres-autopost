"""Telegram captions (HTML, max 1024 chars for photos). Order: Turkish, English, Persian."""
import html

from light import CITIES, CONDITIONS, dates  # from ghebres/scripts

LIMIT = 1024


def h(s):
    return html.escape(str(s or ""), quote=False)


def footer(cfg, source=None, link=None):
    t = cfg.get("telegram", {})
    parts = []
    if source:
        src = f'<a href="{h(link)}">{h(source)}</a>' if link else h(source)
        parts.append(f"🔗 Kaynak · Source · منبع: {src}")
    parts.append(f'📲 <a href="{t.get("telegram_link")}">Telegram</a> · <a href="{t.get("instagram_link")}">Instagram</a>')
    return "\n".join(parts)


def date_line(spec):
    tr, en, fa = dates(spec)
    return f"📅 {h(tr)} | {h(en)} | {h(fa)}"


def fit(blocks, tail):
    """Join blocks; drop/trim from the end of the optional ones until it fits Telegram's limit."""
    text = "\n\n".join(b for b in blocks if b) + "\n\n" + tail
    while len(text) > LIMIT and len(blocks) > 1:
        blocks = blocks[:-1]
        text = "\n\n".join(b for b in blocks if b) + "\n\n" + tail
    return text[:LIMIT]


def weather(cfg, spec, evening):
    head = ("🌤 <b>Kuzey Kıbrıs’ta Yarın Hava Durumu</b>\n<b>Tomorrow’s Weather in Northern Cyprus</b>\n<b>پیش‌بینی هوای فردا در قبرس شمالی</b>"
            if evening else
            "🌤 <b>Kuzey Kıbrıs’ta Hava Durumu</b>\n<b>Weather in Northern Cyprus</b>\n<b>وضعیت آب و هوای قبرس شمالی</b>")
    rows = []
    for it in spec["items"]:
        c = CITIES.get(it["city"], {"tr": it["city"], "fa": it["city"]})
        en, tr, fa = CONDITIONS.get(it["condition"], ("", "", ""))
        rows.append(f"• <b>{h(c['tr'])}</b> {it['temp']}°/{it['low']}° — {h(tr)} · {h(en)} · {h(fa)} ({h(c['fa'])})")
    sun = f"☀️ {spec['sunrise']} · 🌙 {spec['sunset']}" if spec.get("sunrise") else ""
    tags = "#KKTC #KuzeyKıbrıs #HavaDurumu #قبرس_شمالی #آب_و_هوا"
    return fit([head + "\n" + date_line(spec), "\n".join(rows), sun, tags], footer(cfg, "Open-Meteo"))


def pharmacy(cfg, spec):
    head = "💊 <b>Nöbetçi Eczaneler</b>\n<b>On Duty Pharmacies</b>\n<b>داروخانه‌های کشیک</b>"
    groups = {}
    for it in spec["items"]:
        groups.setdefault(it["city"], []).append(it)
    blocks = [head + "\n" + date_line(spec)]
    for key, items in groups.items():
        c = CITIES.get(key, {"tr": key, "en": key, "fa": key})
        lines = [f"📍 <b>{h(c['tr'])}</b> · {h(c['en'])} · {h(c['fa'])}"]
        for it in items:
            hrs = f" ({h(it['hours'])})" if it.get("hours") else ""
            lines.append(f"• {h(it['name'])} — {h(it['phone'])}{hrs}")
        blocks.append("\n".join(lines))
    blocks.append("🚑 Acil · Emergency · اورژانس: 112\n#KKTC #NöbetçiEczane #قبرس_شمالی #داروخانه_کشیک")
    tail = footer(cfg, spec.get("source", "kteb.org"), cfg["pharmacy"]["url"])
    text = "\n\n".join(blocks) + "\n\n" + tail
    if len(text) <= LIMIT:
        return text
    # too long: keep names + phones only
    short = [blocks[0]]
    for key, items in groups.items():
        c = CITIES.get(key, {"tr": key})
        short.append(f"📍 <b>{h(c['tr'])}</b>: " + " · ".join(f"{h(i['name'].replace(' Eczanesi', ''))} {h(i['phone'])}" for i in items))
    return fit(short, tail)


def news(cfg, spec, meta):
    tr, en, fa = spec["tr"], spec["en"], spec["fa"]
    tags = " ".join("#" + t.strip("#").replace(" ", "_") for t in (meta.get("hashtags_fa") or [])[:4])
    tags = ("#KKTC #KuzeyKıbrıs #قبرس_شمالی " + tags).strip()
    blocks = [
        f"🇹🇷 <b>{h(tr['title'])}</b>\n{h(tr['body'])}",
        f"🇬🇧 <b>{h(en['title'])}</b>\n{h(en['body'])}",
        f"🇮🇷 <b>{h(fa['title'])}</b>\n{h(fa['body'])}",
        tags,
    ]
    tail = footer(cfg, meta.get("source"), meta.get("link"))
    text = "\n\n".join(blocks) + "\n\n" + tail
    if len(text) <= LIMIT:
        return text
    # shorten: keep Persian in full, titles only for TR/EN
    blocks = [f"🇹🇷 <b>{h(tr['title'])}</b>", f"🇬🇧 <b>{h(en['title'])}</b>",
              f"🇮🇷 <b>{h(fa['title'])}</b>\n{h(fa['body'])}", tags]
    return fit(blocks, tail)
