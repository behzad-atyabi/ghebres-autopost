import datetime as dt
import logging
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ghebres" / "scripts"))

log = logging.getLogger("ghebres")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

UA = "Mozilla/5.0 (compatible; GhebresBot/1.0; +https://t.me/ghebres_official)"


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def now_local(cfg):
    fake = os.environ.get("FAKE_NOW")  # e.g. 2026-11-03T08:05 for testing
    tz = ZoneInfo(cfg.get("timezone", "Europe/Nicosia"))
    if fake:
        return dt.datetime.fromisoformat(fake).replace(tzinfo=tz)
    return dt.datetime.now(tz)


def http():
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "tr,en;q=0.8"})
    # slow or briefly unavailable sites (weather API, news feeds, kteb.org) get 3 more tries, 3s/6s/12s apart;
    # only GET/HEAD are retried, so nothing is ever posted twice
    retry = Retry(total=3, connect=3, read=3, status=3, backoff_factor=3,
                  status_forcelist=(500, 502, 503, 504), allowed_methods=("GET", "HEAD"), raise_on_status=False)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def env(name, required=False):
    v = os.environ.get(name, "").strip()
    if required and not v:
        raise RuntimeError(f"missing secret/env {name}")
    return v
