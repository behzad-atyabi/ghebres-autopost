"""Hosting (media branch), Telegram channel, Instagram stories, and run state."""
import datetime as dt
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests

from .common import ROOT, env, log

MEDIA = ROOT / "_media"
KEEP_DAYS = 3


# ------------------------------------------------------------------ media branch (public image URLs + state)
def _git(*args, cwd=MEDIA, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def _remote():
    repo = env("GITHUB_REPOSITORY", required=True)
    token = env("GITHUB_TOKEN", required=True)
    return repo, f"https://x-access-token:{token}@github.com/{repo}.git"


def media_open():
    """Fetch the 'media' branch into _media (or start it). Returns state dict."""
    if MEDIA.exists():
        shutil.rmtree(MEDIA)
    if not env("GITHUB_REPOSITORY"):
        MEDIA.mkdir()
        log.info("no GITHUB_REPOSITORY: local mode, state kept in _media/")
        local = ROOT / ".local_state.json"
        return json.loads(local.read_text()) if local.exists() else {}
    _, url = _remote()
    r = subprocess.run(["git", "clone", "--depth", "1", "-b", "media", url, str(MEDIA)], capture_output=True, text=True)
    if r.returncode != 0:
        log.info("media branch not found, it will be created")
        MEDIA.mkdir()
    st = MEDIA / "state.json"
    return json.loads(st.read_text()) if st.exists() else {}


def media_add(paths, now):
    """Copy images into the media tree; returns their future public URLs."""
    rel_dir = Path(f"{now:%Y/%m/%d}")
    (MEDIA / rel_dir).mkdir(parents=True, exist_ok=True)
    urls = []
    repo = env("GITHUB_REPOSITORY") or "local/local"
    for p in paths:
        dest = rel_dir / Path(p).name
        shutil.copy(p, MEDIA / dest)
        urls.append(f"https://raw.githubusercontent.com/{repo}/media/{dest.as_posix()}")
    return urls


def media_save(state, now):
    """Write state, prune old images, force-push a single-commit 'media' branch (keeps the repo small)."""
    state["updated"] = now.isoformat()
    state["news_seen"] = state.get("news_seen", [])[-800:]
    state["news_recent_titles"] = state.get("news_recent_titles", [])[-40:]
    done = state.get("done", {})
    cutoff = (now - dt.timedelta(days=4)).strftime("%Y-%m-%d")
    state["done"] = {k: v for k, v in done.items() if k[:10] >= cutoff}
    (MEDIA / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1))
    limit = (now - dt.timedelta(days=KEEP_DAYS)).date()
    for d in MEDIA.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]"):
        try:
            if dt.date(int(d.parts[-3]), int(d.parts[-2]), int(d.parts[-1])) < limit:
                shutil.rmtree(d)
        except ValueError:
            pass
    if not env("GITHUB_REPOSITORY"):
        (ROOT / ".local_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1))
        return
    _, url = _remote()
    if (MEDIA / ".git").exists():
        shutil.rmtree(MEDIA / ".git")
    _git("init", "-q")
    _git("checkout", "-q", "-b", "media")
    _git("config", "user.name", "ghebres-bot")
    _git("config", "user.email", "ghebres-bot@users.noreply.github.com")
    _git("add", "-A")
    _git("commit", "-q", "-m", f"media {now:%Y-%m-%d %H:%M}")
    _git("push", "-q", "-f", url, "media")


def wait_public(urls, timeout=90):
    for u in urls:
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                r = requests.head(u, timeout=15)
                if r.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(5)
        else:
            raise RuntimeError(f"image not reachable: {u}")


# ------------------------------------------------------------------ Telegram
def tg(method, **kw):
    token = env("TELEGRAM_BOT_TOKEN", required=True)
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", timeout=120, **kw)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"telegram {method}: {data.get('description')}")
    return data["result"]


def telegram_post(paths, caption):
    chat = env("TELEGRAM_CHANNEL", required=True)
    if len(paths) == 1:
        with open(paths[0], "rb") as f:
            tg("sendPhoto", data={"chat_id": chat, "caption": caption, "parse_mode": "HTML"}, files={"photo": f})
        return
    files, media = {}, []
    for i, p in enumerate(paths[:10]):
        files[f"f{i}"] = open(p, "rb")
        m = {"type": "photo", "media": f"attach://f{i}"}
        if i == 0:
            m.update(caption=caption, parse_mode="HTML")
        media.append(m)
    try:
        tg("sendMediaGroup", data={"chat_id": chat, "media": json.dumps(media)}, files=files)
    finally:
        for f in files.values():
            f.close()


def alert(text):
    chat = env("TELEGRAM_ADMIN_CHAT")
    if not chat or not env("TELEGRAM_BOT_TOKEN"):
        return
    try:
        tg("sendMessage", data={"chat_id": chat, "text": f"⚠️ GHEBRES autopost\n{text}"[:4000]})
    except Exception as ex:
        log.warning("alert failed: %s", ex)


# ------------------------------------------------------------------ Instagram (Graph API, Business/Creator account)
def ig_story(cfg, image_url):
    ver = cfg.get("instagram", {}).get("graph_version", "v23.0")
    uid = env("IG_USER_ID", required=True)
    token = env("IG_ACCESS_TOKEN", required=True)
    base = f"https://graph.facebook.com/{ver}"
    r = requests.post(f"{base}/{uid}/media", data={"image_url": image_url, "media_type": "STORIES",
                                                   "access_token": token}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"instagram container: {r.get('error', r)}")
    cid = r["id"]
    for _ in range(24):
        s = requests.get(f"{base}/{cid}", params={"fields": "status_code", "access_token": token}, timeout=30).json()
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"instagram processing: {s}")
        time.sleep(5)
    p = requests.post(f"{base}/{uid}/media_publish", data={"creation_id": cid, "access_token": token}, timeout=60).json()
    if "id" not in p:
        raise RuntimeError(f"instagram publish: {p.get('error', p)}")
    return p["id"]


def dry_run(cfg):
    v = os.environ.get("DRY_RUN", "").lower()
    if v in ("1", "true", "yes"):
        return True
    if v in ("0", "false", "no"):
        return False
    return bool(cfg.get("publish", {}).get("dry_run"))
