---
name: ghebres-brand
description: Produce GHEBRES OFFICIAL content for Northern Cyprus - trilingual (Turkish, English, Persian) Instagram stories for news, weather and duty pharmacies in a bright Mediterranean style, plus navy-and-gold breaking-news and quote cards and Instagram/Telegram captions. Use for any GHEBRES story, post, news card, weather card, duty-pharmacy list or caption for ghebres_official.
---

# GHEBRES OFFICIAL – brand content skill

GHEBRES OFFICIAL is a Persian-language news and information reference for Northern Cyprus,
published on Instagram (@ghebres_official) and Telegram (t.me/ghebres_official).
Every image must look like it came from the same newsroom: dark navy, gold accents,
Vazirmatn font, right-to-left layout, handle and Telegram link in the footer.

## Workflow

1. **Gather and verify.** Get the facts from a named source (a news site, ministry, kteb.org, etc.).
   Never invent numbers, names, phone numbers or dates. If something can't be confirmed, leave it out
   or say "according to <source>".
2. **Write the Persian copy** (rules below).
3. **Write a JSON spec** and render it with `scripts/render.py` (see Layouts).
4. **Look at every PNG** before delivering. Check that text isn't cut off, Persian letters are joined,
   and Latin names / phone numbers read left-to-right.
5. **Write captions** for Instagram and Telegram (templates below) and deliver images + captions together.

## Rendering

```bash
pip install playwright   # once, if missing
python -m playwright install chromium   # once, if no Chrome on the machine
python3 scripts/render.py spec.json -o out/
```

The script falls back to a locally installed Google Chrome / Chromium if Playwright's own browser
isn't installed (`CHROME_PATH` env var overrides). Fonts are embedded, so nothing needs installing.
A spec file may hold one object or a list of objects. Output names come from `"name"`.
`--html-only` writes the HTML without rendering (useful for debugging).

### Formats
| format | size | use |
|---|---|---|
| `story` | 1080×1920 | Instagram story, Telegram image (default) |
| `post` | 1080×1350 | Instagram feed post (4:5) |
| `square` | 1080×1080 | square post, Telegram preview |

### Layouts and fields
Common fields: `name`, `layout`, `format`, `date` (Persian, e.g. "سه‌شنبه ۱۲ آبان ۱۴۰۵"),
`category` (gold pill), `title`, `subtitle`, `source`, `logo` (path to another PNG; default is the
brand logo `assets/logo.png` shown beside the GHEBRES OFFICIAL wordmark; `false` hides it), `persian_digits` (default true).

In `title`, wrap the key words in `*asterisks*` to colour them gold: `"افزایش *حداقل دستمزد*"`.
Use it on one to three words, never the whole title.

- **`news`** – standard news card. Extra: `body` (string with `\n` between paragraphs, or a list),
  `image` (path to a photo; shown above the title on story/post).
- **`list`** – numbered cards: duty pharmacies, rankings, schedules, prices.
  `items`: list of `{title, subtitle, meta, phone, tag, rank}` (all optional except `title`).
  `numbered` (default true), `per_page` (default story 5, post 3, square 2).
  Long lists split automatically into `name_1.png`, `name_2.png` … with "۱ / ۲" page markers.
- **`breaking`** – urgent news, centred, red "خبر فوری" pill (override with `category`).
- **`quote`** – a statement by an official; `title` is the quote, `by` is who said it.

### Light "Mediterranean" theme – DEFAULT for news, weather and duty pharmacies
Bright sky-and-sea look, white cards, navy text, trilingual Turkish / English / Persian, logo and
GHEBRES OFFICIAL at the top right, Telegram call-to-action bar at the bottom. Story format only
(1080×1920). Use these three layouts for daily news, weather and pharmacies; use the navy layouts
above for breaking news, quotes and anything else.

Dates: give `"date": "YYYY-MM-DD"` and the Turkish, English and Persian (Jalali) dates are written
automatically, e.g. "3 Kasım 2026 (Salı)", "November 3, 2026 (Tuesday)", "سه‌شنبه ۱۲ آبان ۱۴۰۵".
Override with `date_tr` / `date_en` / `date_fa` if needed.

City keys (used for names in three languages, region colours and thumbnail photos):
`lefkosa, girne, magusa, iskele, guzelyurt, lefke, karpaz` (English/Turkish names also accepted).

- **`weather`** – Mediterranean poster: sky with sun glow, big weather icon beside a two-line Turkish headline,
  EN and FA titles, Kyrenia harbour photo, frosted-glass city rows over the sea, bougainvillea, "hottest" and
  sunrise/sunset chips, script slogan. Sky and headline icon follow the dominant condition (sunny / cloudy / rain).
  `items`: `{city, temp, low, condition}`; condition one of `sunny, partly, cloudy, rain, storm, fog, wind`.
  Six cities. Optional `sunrise`, `sunset`, `title_tr/title_en/title_fa`, `image` (another harbour/landscape photo).
  Older variants: `weather_map` (island map with bubbles), `weather_classic` (plain list).
- **`news3`** – one story told in three languages: `tr`, `en`, `fa`, each `{title, body}`
  (any of them may be omitted). `icon` for the Turkish card: `news, ship, plane, car, health, money,
  alert, building` or `flag` (Turkish flag). `tab` changes the red "GÜNÜN HABERİ" label. `source` required.
  Keep each body to 2–3 sentences; text shrinks to fit but long text gets small.
- **`pharmacy`** – night scene (moon, stars, harbour at dusk) with a glowing green pharmacy-cross sign and
  a red "ACİL 112" badge; pharmacies grouped by region in coloured cards. `items`: `{city, name, address, phone, hours}`.
  Regions: the city keys above plus `ustmesarya`, `altmesarya`. Pages are split and balanced automatically;
  regions are not split across pages unless one region alone is longer than a page.
  Always `"source": "kteb.org"`. `pharmacy_classic` is the older daylight layout.

Language order everywhere: **Turkish, English, Persian**. Date order: Turkish, Gregorian (English), Jalali (Persian).

Photos: `assets/photos/` holds two harbour hero bands and one thumbnail per city. Pass `image` (a path)
to use a different hero photo — e.g. a photo of the actual news location. Never use a photo of a real
person without the user providing it.

See `examples/light-samples.json` for working examples of all three.

Text shrinks automatically to fit. If a title still looks crowded, shorten it — don't fight the layout.
See `examples/samples.json` for one working example of every layout.

### Digits
Persian digits (۱۲۳) are applied only to text containing Persian letters. Latin text — Turkish
addresses, "No:12", phone numbers — keeps Latin digits on purpose. Phone numbers go in `phone`,
never inside Persian text, so they render left-to-right.

## Persian copy rules

- Neutral, factual news tone. No exaggeration, no clickbait, no emojis inside images.
- Title: one clear sentence, ideally under 12 words, saying what happened.
- Body on a story: 2–3 short paragraphs maximum. Detail goes in the caption, not the image.
- Place names: Persian first, Turkish name in parentheses the first time —
  گیرنه (Girne), نیکوزیا (Lefkoşa), فاماگوستا (Gazimağusa), ایسکله (İskele), گوزل‌یورت (Güzelyurt),
  لفکه (Lefke). Keep Turkish names of businesses (Eczane Merkez) as they are.
- Use the half-space (ZWNJ, U+200C) correctly: می‌شود، داروخانه‌ها، شده‌اند.
- Money: write the currency in Persian — ۲۵٬۰۰۰ لیر ترکیه، ۱۵۰ یورو.
- Always fill `source` for news. For official data (pharmacies, prices) name the issuing body.

## Captions

**Instagram**
```
<title as one line>

<2–4 sentences of detail>

📍 <city / region>
🔗 منبع: <source>

اخبار و اطلاعات کاربردی قبرس شمالی را در تلگرام دنبال کنید: t.me/ghebres_official

#قبرس_شمالی #قبرس #GHEBRES #<topic>
```
Use 5–10 hashtags, Persian first, then a few English/Turkish ones (#NorthCyprus #KKTC) only when relevant.

**Telegram** – the same text without hashtags except #قبرس_شمالی, with the bold title (`**…**`),
and the Instagram link at the end instead of the Telegram one: instagram.com/ghebres_official.

## Brand tokens

Defined once at the top of `scripts/render.py` (`BRAND` dict). Change them there and every layout follows.

| token | value | role |
|---|---|---|
| navy_deep / navy / navy_soft | #050E1C / #0A1A30 / #13284A | background gradient |
| gold / gold_soft / gold_dim | #D6B04C / #EBD08A / #8C7428 | accents, highlights, frame |
| text / text_dim | #F4F1E8 / #A9B4C6 | body text, meta |
| red | #C0392B | breaking-news pill only |

Logo: `assets/logo.png` – gold "G" with Cyprus map, buildings, palm and waves (transparent PNG).
Never recolour, stretch or crop it.

Fonts: Vazirmatn (SIL Open Font License, `assets/fonts/OFL.txt`); Dancing Script for the weather slogan
(SIL OFL, `assets/fonts/OFL-DancingScript.txt`).
