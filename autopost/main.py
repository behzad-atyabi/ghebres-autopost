"""Hourly entry point. Decides what to publish this hour, builds images, posts to Instagram story + Telegram.

Env:
  TASK     auto (default) | weather | pharmacy | news | all
  DRY_RUN  1 = build only, publish nothing (images land in out/)
  FORCE    1 = ignore 'already published this slot'
  FAKE_NOW e.g. 2026-11-03T08:05 (testing)
"""
import datetime as dt
import os
import sys
import traceback

from .common import ROOT, load_config, log, now_local
from . import captions, publish

import render  # ghebres/scripts/render.py (path set in common)

OUT = ROOT / "out"


def due(cfg, now, state, task):
    """Return list of (task, slot_key) to run now."""
    sch = cfg["schedule"]
    forced = os.environ.get("TASK", "auto").lower()
    force = os.environ.get("FORCE", "") in ("1", "true", "yes")
    done = state.get("done", {})
    jobs = []
    catch = int(sch.get("catch_up_hours", 1))

    def slot_for(hours):
        for h in hours:
            for back in range(catch + 1):
                t = now - dt.timedelta(hours=back)
                if t.hour == h and t.date() == (now - dt.timedelta(hours=back)).date():
                    return f"{t:%Y-%m-%d}T{h:02d}"
        return None

    for name, hours_key in (("weather", "weather_hours"), ("pharmacy", "pharmacy_hours")):
        if forced in (name, "all"):
            jobs.append((name, f"{now:%Y-%m-%dT%H}-manual"))
        elif forced == "auto":
            key = slot_for(sch.get(hours_key, []))
            if key and (force or f"{name}:{key}" not in done):
                jobs.append((name, key))
    if forced in ("news", "all"):
        jobs.append(("news", f"{now:%Y-%m-%dT%H}-manual"))
    elif forced == "auto" and now.hour in sch.get("news_hours", []):
        key = f"{now:%Y-%m-%dT%H}"
        if force or f"news:{key}" not in done:
            jobs.append(("news", key))
    return [(n, k) for n, k in jobs if task in ("any", n)]


def build(spec):
    OUT.mkdir(exist_ok=True)
    return render.render(spec, OUT)


def ship(cfg, now, paths, caption, label):
    if publish.dry_run(cfg):
        log.info("[dry-run] %s → %s\n--- caption (%d chars) ---\n%s", label, paths, len(caption), caption)
        return
    pub = cfg.get("publish", {})
    errors = []
    if pub.get("telegram", True):
        try:
            publish.telegram_post(paths, caption)
            log.info("telegram ok: %s", label)
        except Exception as ex:
            errors.append(f"Telegram ({label}): {ex}")
    if pub.get("instagram_story", True):
        try:
            urls = publish.media_add(paths, now)
            publish.media_save(STATE, now)  # push images so Instagram can fetch them
            publish.wait_public(urls)
            for u in urls:
                publish.ig_story(cfg, u)
            log.info("instagram ok: %s (%d stories)", label, len(urls))
        except Exception as ex:
            errors.append(f"Instagram ({label}): {ex}")
    if errors:
        raise RuntimeError("; ".join(errors))


STATE = {}


def main():
    global STATE
    cfg = load_config()
    now = now_local(cfg)
    STATE = publish.media_open()
    jobs = due(cfg, now, STATE, "any")
    log.info("now %s → jobs %s", now.isoformat(timespec="minutes"), jobs)
    failures = []
    for name, key in jobs:
        try:
            if name == "weather":
                from . import weather
                spec, evening = weather.fetch(cfg, now)
                ship(cfg, now, build(spec), captions.weather(cfg, spec, evening), name)
            elif name == "pharmacy":
                from . import pharmacy
                spec = pharmacy.fetch(cfg, now)
                ship(cfg, now, build(spec), captions.pharmacy(cfg, spec), name)
            elif name == "news":
                from . import news
                res = news.make(cfg, now, STATE)
                if res:
                    spec, meta = res
                    ship(cfg, now, build(spec), captions.news(cfg, spec, meta), name)
            if not publish.dry_run(cfg):
                STATE.setdefault("done", {})[f"{name}:{key}"] = now.isoformat(timespec="minutes")
        except Exception as ex:
            log.error("%s failed: %s\n%s", name, ex, traceback.format_exc())
            failures.append(f"{name}: {ex}")
    if not publish.dry_run(cfg) or not os.environ.get("GITHUB_REPOSITORY"):
        publish.media_save(STATE, now)
    if failures:
        publish.alert("\n".join(failures))
        sys.exit(1)


if __name__ == "__main__":
    main()
