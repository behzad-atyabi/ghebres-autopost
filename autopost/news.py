"""Hourly news: collect fresh stories from RSS, let Claude pick one and write it in TR / EN / FA."""
import calendar
import datetime as dt
import hashlib
import json
import re

import feedparser
from bs4 import BeautifulSoup

from .common import env, http, log

ICONS = ["news", "ship", "plane", "car", "health", "money", "alert", "building"]


def norm_key(title):
    t = re.sub(r"[^\wçğıöşüâîû]+", " ", title.lower())
    return hashlib.sha1(" ".join(t.split())[:80].encode()).hexdigest()[:16]


def clean_html(s):
    return " ".join(BeautifulSoup(s or "", "html.parser").get_text(" ").split())


def collect(cfg, now, seen):
    ncfg = cfg["news"]
    cutoff = now.timestamp() - ncfg.get("max_age_hours", 6) * 3600
    sess = http()
    out, report = [], []
    for src in ncfg["sources"]:
        try:
            r = sess.get(src["url"], timeout=25)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            n = 0
            for e in feed.entries[:40]:
                ts = None
                for k in ("published_parsed", "updated_parsed"):
                    if e.get(k):
                        ts = calendar.timegm(e[k])
                        break
                if ts and ts < cutoff:
                    continue
                title = clean_html(e.get("title", ""))
                source = src["name"]
                # Google News titles end with " - Outlet"
                if "news.google." in src["url"] and " - " in title:
                    title, source = title.rsplit(" - ", 1)
                key = norm_key(title)
                if not title or key in seen:
                    continue
                out.append({"key": key, "title": title, "source": source, "link": e.get("link", ""),
                            "summary": clean_html(e.get("summary", ""))[:500],
                            "published": dt.datetime.utcfromtimestamp(ts).isoformat() + "Z" if ts else ""})
                n += 1
            report.append(f"{src['name']}: {n}")
        except Exception as ex:  # a broken feed must not stop the run
            report.append(f"{src['name']}: FAILED ({type(ex).__name__})")
    log.info("news feeds: %s", "; ".join(report))
    uniq, keys = [], set()
    for c in out:
        if c["key"] not in keys:
            keys.add(c["key"])
            uniq.append(c)
    return uniq[:40], report


def article_text(url):
    if not url or "news.google." in url:
        return ""
    try:
        r = http().get(url, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer", "header", "aside"]):
            t.decompose()
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        paras = [p for p in paras if len(p) > 50]
        return "\n".join(paras)[:4000]
    except Exception:
        return ""


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY", required=True))


def _json(text):
    a, b = text.find("{"), text.rfind("}")
    return json.loads(text[a:b + 1])


def _ask(cfg, system, user, max_tokens=1500):
    msg = _client().messages.create(
        model=cfg["news"].get("model", "claude-sonnet-5-5"), max_tokens=max_tokens,
        system=system, messages=[{"role": "user", "content": user}])
    return "".join(getattr(b, "text", "") for b in msg.content)


PICK_SYS = """You are the news editor of GHEBRES OFFICIAL, a Persian-language news page about Northern Cyprus (KKTC).
Choose the single most useful and newsworthy story for this hour. Prefer: concrete, verifiable, local to Northern Cyprus,
useful to the audience. Avoid: duplicates of recently posted stories (same event = duplicate), opinion columns, gossip,
astrology, ads, sports results of minor leagues, stories about private individuals' tragedies, graphic violence.
Reply with JSON only: {"pick": <index or null>, "reason": "<short>"}"""

WRITE_SYS = """You write short news cards for GHEBRES OFFICIAL (Northern Cyprus news, Instagram stories + Telegram).
Rules:
- Use ONLY facts in the provided source text. Never add numbers, names, dates or causes that are not there.
- Neutral, factual tone. No opinion, no emojis, no clickbait.
- Do not name private individuals involved in crimes or accidents; officials and institutions are fine.
- Three languages, in this order: Turkish (tr), English (en), Persian (fa).
- title: one clear sentence, max 70 characters. body: 2-3 short sentences, max 260 characters.
- Persian: natural Iranian Persian, correct half-spaces (ZWNJ, e.g. می‌شود), Persian place names
  (نیکوزیا, گیرنه, فاماگوستا, ایسکله, گوزل‌یورت, لفکه, کارپاز). Keep brand/institution names readable.
- icon: one of news, ship, plane, car, health, money, alert, building.
- If the source text is too thin to write a correct summary, return {"skip": true}.
Reply with JSON only:
{"tr":{"title":"","body":""},"en":{"title":"","body":""},"fa":{"title":"","body":""},"icon":"news","hashtags_fa":["",""]}"""


def make(cfg, now, state):
    seen = set(state.get("news_seen", []))
    cands, report = collect(cfg, now, seen)
    if not cands:
        log.info("news: nothing new")
        return None
    recent = state.get("news_recent_titles", [])[-20:]
    listing = "\n".join(f"[{i}] ({c['source']}, {c['published']}) {c['title']} — {c['summary'][:200]}"
                        for i, c in enumerate(cands))
    pick = _json(_ask(cfg, PICK_SYS,
                      f"Audience: {cfg['news'].get('audience', '')}\n\nRecently posted (do not repeat):\n"
                      + "\n".join(f"- {t}" for t in recent) + f"\n\nCandidates:\n{listing}", 300))
    idx = pick.get("pick")
    if idx is None or not (0 <= int(idx) < len(cands)):
        log.info("news: editor skipped this hour (%s)", pick.get("reason"))
        # remember them so the same weak items are not re-evaluated every hour
        state.setdefault("news_seen", []).extend(c["key"] for c in cands)
        return None
    c = cands[int(idx)]
    body = article_text(c["link"])
    src_text = f"Headline: {c['title']}\nOutlet: {c['source']}\nRSS summary: {c['summary']}\n\nArticle text:\n{body or '(not available)'}"
    out = _json(_ask(cfg, WRITE_SYS, src_text, 1500))
    state.setdefault("news_seen", []).append(c["key"])
    if out.get("skip"):
        log.info("news: writer skipped thin story: %s", c["title"])
        return None
    icon = out.get("icon") if out.get("icon") in ICONS else "news"
    spec = {"name": f"news_{now:%Y%m%d_%H}", "layout": "news3", "date": now.date().isoformat(),
            "icon": icon, "source": c["source"], "tr": out["tr"], "en": out["en"], "fa": out["fa"]}
    meta = {"link": c["link"], "source": c["source"], "hashtags_fa": out.get("hashtags_fa", [])}
    state.setdefault("news_recent_titles", []).append(out["tr"]["title"])
    return spec, meta
