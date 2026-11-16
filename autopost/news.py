"""Hourly news: collect fresh stories from RSS, pick one and publish it in TR / EN / FA.

Writers, in order of preference:
- ANTHROPIC_API_KEY set -> Claude picks the story and writes the three versions (paid API).
- GEMINI_API_KEY set    -> Google Gemini (free tier) does the same job.
- neither, or the AI call fails -> free mode: keyword-based pick + Google Translate (deep-translator).
"""
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


def _ask_claude(cfg, system, user, max_tokens):
    msg = _client().messages.create(
        model=cfg["news"].get("model", "claude-sonnet-5-5"), max_tokens=max_tokens,
        system=system, messages=[{"role": "user", "content": user}])
    return "".join(getattr(b, "text", "") for b in msg.content)


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"


_GEMINI_MODELS = None


def _gemini_models(cfg, key):
    """Ask Google which models this key can use; prefer the configured ones, then any text 'flash' model."""
    global _GEMINI_MODELS
    if _GEMINI_MODELS is not None:
        return _GEMINI_MODELS
    wanted = cfg["news"].get("gemini_models") or []
    avail = []
    try:
        r = http().get("https://generativelanguage.googleapis.com/v1beta/models",
                       params={"pageSize": 200}, headers={"x-goog-api-key": key}, timeout=30)
        r.raise_for_status()
        for m in r.json().get("models", []):
            name = m.get("name", "").split("/")[-1]
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            if "flash" not in name or any(x in name for x in ("image", "tts", "audio", "live", "embed", "vision")):
                continue
            avail.append(name)
    except Exception as ex:
        log.warning("gemini: could not list models (%s)", ex)
    def rank(n):  # configured first, then stable before preview/exp, full before lite, newest name first
        return (wanted.index(n) if n in wanted else 99, "preview" in n or "exp" in n, "lite" in n)
    ordered = sorted(sorted(set(avail), reverse=True), key=rank)
    _GEMINI_MODELS = ordered[:4] or wanted or ["gemini-flash-latest"]
    log.info("gemini models to try: %s", ", ".join(_GEMINI_MODELS))
    return _GEMINI_MODELS


def _ask_gemini(cfg, system, user, max_tokens):
    key = env("GEMINI_API_KEY", required=True)
    models = _gemini_models(cfg, key)
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": max(max_tokens, 2048),
                                 "responseMimeType": "application/json"}}
    import time
    last, tried = None, []
    for m in models:  # first model that answers wins; busy or missing models are skipped
        for attempt in range(3):
            try:
                r = http().post(GEMINI_URL.format(m), json=body, timeout=45,
                                headers={"x-goog-api-key": key, "Content-Type": "application/json"})
            except Exception as ex:  # timeout / connection problem -> treat like "busy"
                last = f"{m}: {type(ex).__name__}"
                time.sleep(5)
                continue
            if r.status_code in (429, 500, 503):  # busy / rate limited -> wait, retry, then next model
                last = f"{m}: HTTP {r.status_code}"
                if attempt == 2:
                    tried.append(last)
                time.sleep(8 * (attempt + 1))
                continue
            break
        else:
            continue
        if r.status_code == 404:
            last = f"{m}: not found"
            tried.append(last)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"gemini {m} HTTP {r.status_code}: {r.text[:300]}")
        parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text:
            last = f"{m}: empty answer"
            continue
        log.info("news: written by %s", m)
        return text
    raise RuntimeError(f"gemini: no usable model ({'; '.join(tried + [last or ''])})")


def _ask(cfg, system, user, max_tokens=1500):
    if env("ANTHROPIC_API_KEY"):
        return _ask_claude(cfg, system, user, max_tokens)
    return _ask_gemini(cfg, system, user, max_tokens)


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


# ------------------------------------------------------------------ free mode (no API key, no cost)
# Practical topics for the audience get a higher score; unsuitable topics are never picked.
BOOST = {
    3: ["ulaşım", "trafik", "yol ", "yolu", "kapalı", "liman", "havaliman", "ercan", "uçuş", "feribot", "otobüs",
        "elektrik", "kesinti", "su kesintisi", "akaryakıt", "benzin", "fiyat", "zam", "asgari ücret", "döviz",
        "sterlin", "euro", "dolar", "ikamet", "vize", "çalışma izni", "öğrenci", "üniversite", "okul", "sınav",
        "sağlık", "hastane", "eczane", "aşı", "hava durumu", "fırtına", "yağış", "sel", "uyarı", "deprem",
        "yangın", "tatil", "bayram", "festival", "etkinlik", "konser"],
    1: ["bakan", "başbakan", "cumhurbaşkanı", "meclis", "hükümet", "ekonomi", "turizm", "belediye", "yatırım",
        "inşaat", "konut", "emlak", "ihracat", "bütçe"],
}
BLOCK = ["burç", "magazin", "cinayet", "intihar", "taciz", "tecavüz", "istismar", "ceset", "öldürül", "bıçak",
         "silahlı", "uyuşturucu", "öldü", "hayatını kaybetti", "yaşamını yitirdi", "kartel", "nefret",
         "düşmanlık", "terör", "köşe yazısı", "yazarımız", "reklam", "sponsor", "iddaa", "bahis", "maç sonucu"]
ICON_WORDS = {"ship": ["liman", "feribot", "gemi", "yat "], "plane": ["havaliman", "ercan", "uçuş", "uçak"],
              "car": ["trafik", "yol ", "yolu", "kaza", "araç", "otobüs", "akaryakıt", "benzin"],
              "health": ["sağlık", "hastane", "eczane", "aşı", "doktor"],
              "money": ["fiyat", "zam", "ücret", "döviz", "sterlin", "euro", "dolar", "ekonomi", "bütçe", "vergi"],
              "alert": ["uyarı", "fırtına", "sel", "yangın", "deprem", "kesinti"],
              "building": ["inşaat", "konut", "emlak", "belediye", "üniversite", "okul", "proje"]}
# Turkish place names -> forms that translate well; then Persian fixes
PLACES_TR = {"Gazimağusa": "Famagusta", "Mağusa": "Famagusta", "Lefkoşa": "Nicosia", "Girne": "Kyrenia",
             "Güzelyurt": "Güzelyurt", "Lefke": "Lefke", "Karpaz": "Karpas"}
FA_FIX = {"کیرنیا": "گیرنه", "کرینیا": "گیرنه", "نیکوزیا": "نیکوزیا", "فاماگوستا": "فاماگوستا",
          "قبرس شمالی ترکیه": "قبرس شمالی", "جمهوری ترک قبرس شمالی": "قبرس شمالی"}


def _low(s):
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def _body_for(c):
    """Real story text: the feed summary, else the first paragraphs of the article page."""
    summ = " ".join((c.get("summary") or "").split())
    if len(summ) >= len(c["title"]) + 40 and summ[:40] != c["title"][:40]:
        return summ
    text = article_text(c.get("link"))
    paras = [p for p in text.split("\n") if len(p) > 80 and p[:40] != c["title"][:40]]
    return " ".join(paras[:2])


def _score(c, recent):
    t = _low(c["title"] + " " + c["summary"])
    if any(b in t for b in BLOCK):
        return None
    words = set(_low(c["title"]).split())
    for r in recent:  # same event already posted -> skip
        rw = set(_low(r).split())
        if words and len(words & rw) / max(len(words), 1) >= 0.6:
            return None
    score = sum(w * sum(1 for k in kws if k in t) for w, kws in BOOST.items())
    letters = [ch for ch in c["title"] if ch.isalpha()]
    if letters and sum(ch.isupper() for ch in letters) / len(letters) > 0.6:  # SHOUTING headline
        score -= 3
    if "kktc" in t or "kıbrıs" in t or any(_low(p) in t for p in PLACES_TR):
        score += 1
    return score


def _sentences(text, limit):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[:end + 1] if end > 60 else cut.rsplit(" ", 1)[0] + "…"


def _translate(text, target):
    import time
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    src = text
    if target == "fa":
        for k, v in PLACES_TR.items():
            src = src.replace(k, v)
    out, errors = "", []
    for attempt in range(3):  # Google often rate-limits shared GitHub servers -> wait and retry
        try:
            out = GoogleTranslator(source="tr", target=target).translate(src) or ""
            if out:
                break
        except Exception as ex:
            errors.append(f"google: {type(ex).__name__}")
            time.sleep(4 * (attempt + 1))
    if not out:
        try:
            codes = {"en": "en-GB", "fa": "fa-IR"}
            out = MyMemoryTranslator(source="tr-TR", target=codes[target]).translate(src[:450]) or ""
        except Exception as ex:
            errors.append(f"mymemory: {type(ex).__name__}")
    if not out:
        raise RuntimeError("; ".join(errors) or "empty translation")
    if target == "fa":
        for k, v in FA_FIX.items():
            out = out.replace(k, v)
    return out.strip()


def make_free(cfg, now, state):
    seen = set(state.get("news_seen", []))
    cands, _ = collect(cfg, now, seen)
    if not cands:
        log.info("news (free): nothing new")
        return None
    recent = state.get("news_recent_titles", [])[-20:]
    scored = [(s, i, c) for i, c in enumerate(cands) if (s := _score(c, recent)) is not None]
    # remember everything looked at, so weak items are not re-checked every hour
    state.setdefault("news_seen", []).extend(c["key"] for c in cands)
    if not scored:
        log.info("news (free): no suitable story this hour")
        return None
    scored.sort(key=lambda x: (-x[0], x[1]))
    c, body = None, ""
    for _, _, cand in scored[:8]:  # best story that actually has text (headline-only items are skipped)
        body = _body_for(cand)
        if len(body) >= 80:
            c = cand
            break
    if c is None:
        log.info("news (free): no story with full text this hour")
        return None
    title = _sentences(c["title"], 110)
    body = _sentences(body, 380)
    tr = {"title": title, "body": body}
    try:
        en = {"title": _translate(title, "en"), "body": _translate(body, "en") if body else ""}
        fa = {"title": _translate(title, "fa"), "body": _translate(body, "fa") if body else ""}
    except Exception as ex:
        log.warning("news (free): translation failed (%s); skipping this hour", ex)
        state["news_seen"] = [k for k in state["news_seen"] if k != c["key"]]  # try again next hour
        return None
    t = _low(title + " " + body)
    icon = next((ic for ic, kws in ICON_WORDS.items() if any(k in t for k in kws)), "news")
    log.info("news (free): picked [%s] %s", c["source"], title)
    spec = {"name": f"news_{now:%Y%m%d_%H}", "layout": "news3", "date": now.date().isoformat(),
            "icon": icon, "source": c["source"], "tr": tr, "en": en, "fa": fa}
    meta = {"link": c["link"], "source": c["source"], "hashtags_fa": ["اخبار_قبرس"]}
    state.setdefault("news_recent_titles", []).append(title)
    return spec, meta


def make(cfg, now, state):
    if not (env("ANTHROPIC_API_KEY") or env("GEMINI_API_KEY")):
        return make_free(cfg, now, state)
    try:
        return make_ai(cfg, now, state)
    except Exception as ex:  # AI down / quota used up -> still post something this hour
        log.warning("news: AI writer failed (%s); using free mode", ex)
        return make_free(cfg, now, state)


def make_ai(cfg, now, state):
    seen = set(state.get("news_seen", []))
    cands, report = collect(cfg, now, seen)
    # headline-only items (Google News links, no summary) cannot give a full story text -> leave them out
    cands = [c for c in cands if "news.google." not in (c.get("link") or "")
             or len(c.get("summary") or "") >= len(c["title"]) + 40]
    if not cands:
        log.info("news: nothing new")
        return None
    recent = state.get("news_recent_titles", [])[-20:]
    listing = "\n".join(f"[{i}] ({c['source']}, {c['published']}) {c['title']} — {c['summary'][:200] or '(headline only)'}"
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
