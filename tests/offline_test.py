"""Offline end-to-end test: network + Claude mocked. Run: DRY_RUN=1 FAKE_NOW=2026-11-03T08:05 python -m tests.offline_test"""
import json, os, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DRY_RUN", "1")
os.environ.setdefault("FAKE_NOW", "2026-11-03T08:05")
os.environ["ANTHROPIC_API_KEY"] = "test"
from autopost import common, news

class R:
    def __init__(self, url):
        self.url = url; self.status_code = 200; self.encoding = "utf-8"
        if "open-meteo" in url:
            mk = lambda mx, mn, c: {"daily": {"weather_code": [c], "temperature_2m_max": [mx], "temperature_2m_min": [mn],
                                   "sunrise": ["2026-11-03T06:21"], "sunset": ["2026-11-03T16:58"], "wind_speed_10m_max": [12]}}
            self._j = [mk(24.3, 14.8, 0), mk(23.1, 16.2, 2), mk(24.0, 14.1, 1), mk(23.4, 15.0, 3), mk(22.2, 12.9, 61), mk(21.8, 14.4, 2)]
            self.text = json.dumps(self._j)
        elif "kteb" in url:
            self.text = open(os.path.join(os.path.dirname(__file__), "kteb_sample.html"), encoding="utf-8").read()
        elif "rss" in url or "news.google" in url:
            self.content = open(os.path.join(os.path.dirname(__file__), "feed_sample.xml"), "rb").read()
            self.text = self.content.decode()
        else:
            self.text = "<html><p>" + "Girne Limanı’nda yat sezonu resmen başladı. Liman idaresi, sezon boyunca yaklaşık 300 teknenin limana gelmesinin beklendiğini açıkladı. " * 2 + "</p></html>"
    def raise_for_status(self): pass
    def json(self): return self._j

class S:
    headers = {}
    def get(self, url, **kw): return R(url + ("?" + "&".join(f"{k}={v}" for k, v in kw.get("params", {}).items()) if kw.get("params") else ""))
common.http = lambda: S()
import autopost.weather, autopost.pharmacy
autopost.weather.http = common.http; autopost.pharmacy.http = common.http; news.http = common.http

def fake_ask(cfg, system, user, max_tokens=1500):
    if system.startswith("You are the news editor"):
        return '{"pick": 0, "reason": "local, practical"}'
    return json.dumps({"tr": {"title": "Girne Limanı’nda yat sezonu başladı", "body": "Girne Limanı’nda yat sezonu resmen başladı. Liman idaresi sezon boyunca yaklaşık 300 tekne beklediğini açıkladı."},
                       "en": {"title": "Yacht season opens at Kyrenia Harbour", "body": "The yacht season has officially opened at Kyrenia Harbour. The port authority expects around 300 boats during the season."},
                       "fa": {"title": "آغاز فصل قایق‌های تفریحی در بندر گیرنه", "body": "فصل قایق‌های تفریحی در بندر گیرنه رسماً آغاز شد. اداره بندر اعلام کرد در این فصل حدود ۳۰۰ قایق انتظار می‌رود."},
                       "icon": "ship", "hashtags_fa": ["گیرنه", "بندر"]})
news._ask = fake_ask

from autopost import main
main.main()
