# Database Plan

## 1) Goals and constraints

* **Keep it tiny** : minimum number of tables; easy to reason about.
* **SQLite-friendly** : no JSON columns; store JSON as `TEXT`.
* **Tier logic in `settings.py`** : `ANON_READS_PER_DAY`, `FREE_READS_PER_DAY`, `STANDARD_READS_PER_DAY`.
* **Anonymous** can open **detail** (metered to 3/day by cookie).
* **No full external bodies** : only store `title`, `summary`, `url`, etc.
* **Search** is basic: `icontains` on `title` and `summary`.
* **Stale badge** uses `MAX(ingested_at)`—no extra table.

---

## 2) Entities and relationships

* **Source** `1 ──> many` **Article**
* **User** `1 ──1` **UserProfile** (holds tier: `free | standard | premium`)
* **User** `1 ──> many` **ReadEvent**
* **Article** `1 ──> many` **ReadEvent**

> Anonymous has  **no DB row** . We meter anonymous reads via a  **signed cookie** .

---

## 3) Tables (fields, constraints, indexes)

### a) `source`

* **Fields**
  * `id` (PK)
  * `name` `TEXT` (required) — e.g., “TechCrunch”
  * `type` `TEXT` (required, enum: `"rss"|"hacker_news"|"guardian"`; MVP: `"rss"`)
  * `url` `TEXT` (required) — feed URL or API base
  * `enabled` `BOOL` (default `true`)
* **Indexes**
  * `(enabled)`
* **Why** : let admin disable a feed without code changes.

---

### b) `article`

* **Fields**
  * `id` (PK)
  * `source_id` (FK → `source.id`,  **PROTECT** ) — keep rows if a source is disabled
  * `title` `VARCHAR(500)` (required)
  * `url` `VARCHAR(1000)` (required) — canonical link to original
  * `summary` `TEXT` (nullable) — short snippet we display
  * `image_url` `VARCHAR(1000)` (nullable)
  * `published_at` `DATETIME` (nullable, stored in UTC)
  * `ingested_at` `DATETIME` (required, default now UTC)
  * `tags` `TEXT` (nullable, JSON-encoded list of strings)
  * `keywords` `TEXT` (nullable, JSON-encoded list of strings; raw from feed)
  * `hash` `CHAR(64)` ( **UNIQUE** , required) — `sha256(canonical_link or link or title)`
* **Indexes**
  * `(-published_at)` — for “latest first”
  * `(title)` — helps `icontains` a bit on SQLite
  * `UNIQUE(hash)` — de-dupe across feeds
* **Why** : minimal fields to render list/detail + cheap dedup + basic search.

---

### c) `user_profile`

* **Fields**
  * `user_id` (PK, 1:1 FK → `auth_user.id`,  **CASCADE** )
  * `tier` `TEXT` (required enum: `"free"|"standard"|"premium"`, default `"free"`)
* **Indexes**
  * `(tier)` — for admin filtering
* **Why** : keep tiers simple. New users default to  **free** .

---

### d) `read_event`

* **Fields**
  * `id` (PK)
  * `user_id` (FK → `auth_user.id`,  **CASCADE** , required)
  * `article_id` (FK → `article.id`,  **CASCADE** , required)
  * `date` `DATE` (required) — **local day** in your app TZ (from `settings.py`, e.g., `America/Chicago`)
  * `created_at` `DATETIME` (required, default now UTC)
* **Constraints**
  * **UNIQUE** `(user_id, article_id, date)` — prevents double counting on refresh/multi-tabs
* **Indexes**
  * `(user_id, date)` — fast “reads today” count
* **Why** : one query gives “reads used today”.

---

## 4) Settings knobs (in `settings.py`)

* `ANON_READS_PER_DAY = 3`  *(cookie-based, no DB)*
* `FREE_READS_PER_DAY = 5`
* `STANDARD_READS_PER_DAY = 11`
* `TTL_MINUTES = 10` *(freshness threshold)*
* `LAZY_REFRESH = True` *(spawn non-blocking ingest after TTL)*
* `FEEDS = [ five RSS URLs … ]`
* `TIER_CONFIG` (minimal): headlines content level per tier
  * `anonymous = "headline"`
  * `free/standard/premium = "summary"`
  * detail enabled for all tiers

> You can allow `.env` to override the numeric values, but config lives in code.

---

## 5) Model responsibilities (what writes what)

* **Source**
  * Seed once (based on `FEEDS`).
  * Admin can toggle `enabled`.
* **Article**
  * Written by the **ingest command** only.
  * Dedup via `hash` upsert.
  * `ingested_at` set on write; `published_at` from feed if available.
* **UserProfile**
  * Auto-create on user signup with `tier="free"`.
  * Admin upgrades to `"standard"` or `"premium"`.
* **ReadEvent**
  * Created only when a **logged-in** user opens  **detail** .
  * Use local date (e.g., `America/Chicago`) computed at request time.
  * Anonymous reads are **not** stored here (cookie only).

---

## 6) Typical queries (what we optimize for)

* **Latest headlines**

  `SELECT ... FROM article ORDER BY published_at DESC LIMIT N`
* **Search**

  `WHERE title ILIKE %q% OR summary ILIKE %q% ORDER BY published_at DESC LIMIT 50`
* **Reads today (logged-in)**

  `SELECT COUNT(*) FROM read_event WHERE user_id=? AND date=?`
* **Stale badge**

  `SELECT MAX(ingested_at) FROM article`

---

## 7) Migrations order

1. `Source`, `Article`
2. `UserProfile` (and **signal** to auto-create profile with tier=`"free"`)
3. `ReadEvent` (with **UNIQUE (user_id, article_id, date)** and **(user_id, date)** index)

> This order lets you run `ingest_news` as soon as Articles exist.

---

## 8) Guardrails (to avoid pain later)

* **On-delete** :
* `Article.source`: **PROTECT** (don’t delete all articles if a source is removed; disable instead)
* `ReadEvent.user/article`: **CASCADE**
* **UTC storage** for all datetimes; convert to local TZ when computing a  **metering `date`** .
* **JSON as TEXT** : keep tags/keywords as JSON strings to stay SQLite-friendly.
* **No M2M tags** : we don’t need that complexity for class.
