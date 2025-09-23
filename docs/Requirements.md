# Requirements Document — Role-Based News App (Class MVP)

Author: John Akujobi

Last Updated: 2025-09-22

Acknowledged (draft): Qwen3-Next-80B-A3B-Thinking (self_hosted)

## 1. Purpose

* Build a **simple, $0-cost** news site for a class demo.
* Support **four tiers** with **metered access** to article details.
* Keep **configuration in `settings.py`** (with a few optional  **`.env` overrides** ).
* Use  **RSS only** , server-rendered Django, and  **SQLite** .

---

## 2. Scope

### In scope

* **Sources:** RSS feeds (e.g., TechCrunch, The Verge, Ars Technica, Wired, Engadget).
* **Tiers (4):**
  * `anonymous` (before signup)
  * `free` (after signup, non-paying)
  * `standard` (simulated subscription via admin toggle)
  * `premium` (admin toggle)
* **Metering:** per-day read limits; counter display; **soft wall** at limit.
* **Pages:** Headlines, Detail, Search, Account.
* **Admin:** Superusers (the 4 teammates) can set user tiers; manage sources.
* **Config:** Hardcoded in `settings.py` with optional environment overrides for a few numbers.
* **DB:** **SQLite** for the demo; optional Postgres if `DATABASE_URL` is set.
* **Auth:** Email + password (no verification).

### Out of scope

* Payments/SSO.
* Non-RSS APIs for MVP.
* Storing full external article bodies (we show **snippet + link-out** only).

---

## 3. Users & Tiers

* **anonymous:** limited full reads/day via cookie; headlines + search allowed.
* **free:** logged-in non-paying; limited full reads/day via DB.
* **standard:** logged-in; higher daily limit (simulated subscription).
* **premium:** logged-in; unlimited (no metering).

> New signups default to  **free** .

---

## 4. Functional Requirements

### 4.1 Configuration (in `settings.py`)

* Define constants:
  * `FEEDS: list[str]` — RSS feed URLs.
  * `ANON_READS_PER_DAY: int` — default **3** (override via `.env` if desired).
  * `FREE_READS_PER_DAY: int` — default  **5** .
  * `STANDARD_READS_PER_DAY: int` — default  **11** .
  * `TTL_MINUTES: int` — default **10** (freshness threshold).
  * `LAZY_REFRESH: bool` — default **True** (non-blocking refresh after TTL).
  * `TIER_CONFIG: dict` — minimal per-tier flags (e.g., headlines content level).
  * Optional UI hint strings (e.g., anonymous/free/standard hints).
* **Changes require a server restart** (no hot reload).
* **Optional `.env` overrides** for the numeric knobs above.

### 4.2 Ingestion

* **Management command** `ingest_news`:
  * Fetch each RSS feed with a short timeout (≈3–5s).
  * Normalize: `title`, `link`, `summary/snippet`, `published`, optional `image`.
  * Compute **dedup hash** (e.g., sha256 of canonical link or link/title); **upsert** by hash.
  * **Tags** : small allow-list mapping; store tags as JSON text on `Article`.
* **Freshness:**
  * Run command manually before demo.
  * If `LAZY_REFRESH` and content is older than `TTL_MINUTES`, **serve immediately** and **kick a non-blocking refresh** (guard against concurrent runs).
  * Show a tiny *“stale”* badge when content age > `TTL_MINUTES`.

### 4.3 Content & Display

* **Headlines page** shows cards with:
  * `anonymous`: **headline** only (title).
  * `free/standard/premium`: **summary** (title + snippet).
* **Detail page** (all tiers enabled):
  * Show our **snippet + “Read on source”** link (no full external body).
* **Allowed categories/sources:** start with “allow all”.

### 4.4 Metering & Soft Wall

* **Count only on Detail page** .
* **anonymous:** best-effort signed cookie `{count}:{YYYYMMDD}` in local timezone.
* **free/standard:** `ReadEvent(user, article, date)` with **unique (user, article, date)** to avoid double counts.
* **premium:** no counting; never walled.
* **Soft wall** triggers at the exact limit; show one wall template with tier-specific CTA text.
* **Reads-left counter** visible on pages where we show it.

### 4.5 Search

* Query param `q`; **basic `icontains`** over `title` + `summary`.
* Return most recent results (cap ~50).

### 4.6 Admin

* All 4 teammates are  **superusers** .
* Admin can:
  * Toggle user tier (`free` / `standard` / `premium`).
  * Enable/disable feeds (via `Source.enabled`).
  * Optionally edit article tags.

---

## 5. Non-Functional Requirements

* **Simplicity:** one Django app; no Celery/Redis; server-rendered templates.
* **Cost:** $0 (RSS + SQLite).
* **Reliability:**
  * On ingest failure, skip the feed and keep last stored content.
  * For anonymous metering, accept cookie resets (class demo).
* **Timezone:** all daily limits use **America/Chicago** boundaries.
* **Licensing:** store headline/snippet/link only.

---

## 6. Data Requirements (schema summary)

* **Source** : `name`, `type ("rss")`, `url`, `enabled`.
* **Article** : `source_id`, `title`, `url`, `summary`, `image_url?`, `published_at`, `tags (JSON text)`, `keywords (JSON text)`, `hash (unique)`, `ingested_at`.
* **User** : Django auth user.
* **UserProfile** : `user_id (1:1)`, `tier ∈ {"free","standard","premium"}` default  **free** .
* **ReadEvent** : `user_id`, `article_id`, `date (local)`, `created_at`;  **unique (user, article, date)** .

**Indexes**

* `Article(published_at DESC)`, `Article(title)`, `ReadEvent(user, date)`.

---

## 7. Endpoints / Pages

* **GET /** — Headlines
  * Enforce simple per-tier display (headline vs summary).
  * Show reads-left counter and any tier hint text.
* **GET /a/** — Detail
  * Apply metering (cookie or DB). On limit → soft wall; else snippet + link-out.
* **GET /search?q=** — Search
  * `icontains` over title + summary; cap results by recency.
* **GET /account** — Account
  * Show current tier and reads left today.
* **/admin/** — Django admin
  * Superusers set user tiers; manage sources; view articles.

---

## 8. Tier Defaults (in `settings.py`)

* `ANON_READS_PER_DAY = 3`
* `FREE_READS_PER_DAY = 5`
* `STANDARD_READS_PER_DAY = 11`
* `PREMIUM` = unlimited (metering disabled)
* Headlines content level:
  * `anonymous = "headline"`, others = `"summary"`.
* Detail page enabled for all tiers.

> Optional `.env` overrides for the numeric limits and `TTL_MINUTES`, `LAZY_REFRESH`.

---

## 9. Acceptance Criteria (MVP)

* Config lives in  **`settings.py`** ; (optional) `.env` can override core numeric limits and refresh knobs.
* RSS ingestion populates articles; duplicates avoided; stale badge appears when applicable.
* **Metering works exactly** :
* `anonymous`: 3 reads/day → soft wall at 4th; resets at local midnight.
* `free`: 5 reads/day → soft wall at 6th.
* `standard`: 11 reads/day → soft wall at 12th.
* `premium`: never soft-walled.
* Headlines, Detail, Search, Account pages render correctly; counters show when enabled.
* Admins can set user tiers and enable/disable sources.
* Runs locally on **SQLite** for the class demo.
