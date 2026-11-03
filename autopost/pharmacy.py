"""Duty pharmacies from kteb.org (server-rendered page)."""
import re
from pathlib import Path

from bs4 import BeautifulSoup

from .common import ROOT, http, log

REGIONS = {
    "LEFKOŞA": "lefkosa", "LEFKOSA": "lefkosa",
    "GİRNE": "girne", "GIRNE": "girne",
    "MAĞUSA": "magusa", "GAZİMAĞUSA": "magusa", "GAZIMAGUSA": "magusa", "MAGUSA": "magusa",
    "GÜZELYURT": "guzelyurt", "GUZELYURT": "guzelyurt",
    "LEFKE": "lefke",
    "İSKELE": "iskele", "ISKELE": "iskele",
    "KARPAZ": "karpaz",
    "ÜST MESARYA": "ustmesarya", "ALT MESARYA": "altmesarya",
}
RE_REGION = re.compile(r"^\s*(.+?)\s+BÖLGES[İI]\s*$")
RE_NAME = re.compile(r"ECZANES[İI]\b")
RE_PHONE = re.compile(r"\(?\b0\s?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b")
RE_HOURS = re.compile(r"\b\d{1,2}[:.]\d{2}\s*[-–]\s*\d{1,2}[:.]\d{2}\b")
RE_DATE = re.compile(r"\b(\d{2})\.(\d{2})\.(\d{4})\b")
SKIP = re.compile(r"^(detay|harita|yol tarifi|telefon|adres|tel|nöbet|nöbetçi eczaneler|tüm bölgeler|ara|"
                  r"pazartesi|salı|çarşamba|perşembe|cuma|cumartesi|pazar)\b", re.I)


def tr_title(s):
    """Turkish-aware Title Case: 'ARZUM DAVULCU ECZANESİ' -> 'Arzum Davulcu Eczanesi'."""
    def low(w):
        return w.replace("I", "ı").replace("İ", "i").lower()

    def up1(w):
        return ("İ" if w[0] == "i" else w[0].upper()) + w[1:] if w else w
    return " ".join(up1(low(w)) for w in s.split())


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    lines = [ln.strip(" \t ") for ln in soup.get_text("\n").split("\n")]
    lines = [ln for ln in lines if ln]
    region = None
    entries, cur = [], None
    page_date = None

    def flush():
        if cur and cur.get("name"):
            entries.append(cur)

    for ln in lines:
        m = RE_REGION.match(ln.upper())
        if m and len(ln) < 40:
            key = REGIONS.get(m.group(1).strip())
            if key:
                flush()
                cur = None
                region = key
                continue
        if region is None:
            continue
        if RE_NAME.search(ln.upper()) and len(ln) < 90 and not RE_PHONE.search(ln):
            flush()
            cur = {"city": region, "name": tr_title(ln.rstrip(".")), "address": "", "phone": "", "hours": ""}
            continue
        if cur is None:
            continue
        d = RE_DATE.search(ln)
        if d and not page_date:
            page_date = f"{d.group(3)}-{d.group(2)}-{d.group(1)}"
        ph = RE_PHONE.search(ln)
        if ph and not cur["phone"]:
            cur["phone"] = re.sub(r"\s+", " ", ph.group(0)).strip()
        hr = RE_HOURS.search(ln)
        if hr and not cur["hours"]:
            cur["hours"] = re.sub(r"\s*[-–]\s*", " - ", hr.group(0)).replace(".", ":")
        rest = RE_HOURS.sub("", RE_PHONE.sub("", RE_DATE.sub("", ln))).strip(" ,.-()|")
        if not cur["address"] and len(rest) > 8 and not SKIP.match(rest) and not rest.isdigit():
            cur["address"] = rest
    flush()
    # de-duplicate (page may repeat blocks for filters)
    seen, uniq = set(), []
    for e in entries:
        k = (e["city"], e["name"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    for e in uniq:
        e["address"] = shorten(e["address"])
    return uniq, page_date


def shorten(addr, limit=70):
    """kteb addresses include directions ('... karşısı, ... yanı'); keep the street + area."""
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    if not parts:
        return addr
    keep = [parts[0]]
    for p in parts[1:]:
        if len(", ".join(keep + [p])) > limit:
            break
        keep.append(p)
    if parts[-1] not in keep and len(", ".join(keep + [parts[-1]])) <= limit + 15:
        keep.append(parts[-1])  # town name is usually last
    return ", ".join(keep)


def fetch(cfg, now):
    url = cfg["pharmacy"]["url"]
    r = http().get(url, timeout=40)
    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    items, page_date = parse(r.text)
    if not items:
        dbg = ROOT / "debug"
        dbg.mkdir(exist_ok=True)
        (dbg / "kteb.html").write_text(r.text, encoding="utf-8")
        raise RuntimeError("kteb.org: no pharmacies parsed (page saved to debug/kteb.html)")
    log.info("pharmacies: %d parsed, page date %s", len(items), page_date)
    spec = {"name": f"pharmacy_{now:%Y%m%d_%H}", "layout": "pharmacy",
            "date": page_date or now.date().isoformat(), "items": items,
            "source": cfg["pharmacy"].get("source_name", "kteb.org")}
    return spec
