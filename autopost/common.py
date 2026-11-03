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
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "tr,en;q=0.8"})
    return s


def env(name, required=False):
    v = os.environ.get(name, "").strip()
    if required and not v:
        raise RuntimeError(f"missing secret/env {name}")
    return v
