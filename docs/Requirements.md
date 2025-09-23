
# Requirements Document — Role-Based News App (Class MVP)

Author - John AKujobi

## 1. Purpose

* Build a **simple, $0-cost** news site for a class demo.
* Support **tier-gated access** to content with  **YAML-driven rules** .
* Prioritize  **simplicity** : one Django app, server-rendered pages,  **no Celery/Redis** .

---

## 2. Scope

### In scope

* **Sources:** RSS feeds only (TechCrunch, The Verge, Ars Technica, Wired, Engadget), configurable in YAML.
* **Tiers (4):**
  * `anonymous` (before signup)
  * `free` (after signup)
  * `standard` (simulated subscription via admin)
  * `premium` (admin toggle)
* **Metering:** daily read limits; displayed counter; soft wall on limit.
* **Pages:** Headlines, Detail, Search, Account, and a superuser **Reload Config** endpoint.
* **Config:** All tier rules, limits, page access, and UI text controlled via  **YAML** .
* **DB:** **SQLite** for demo; optional Postgres if `DATABASE_URL` present.
* **Auth:** Email + password (no email verification).
* **Admin:** All 4 teammates are superusers; can set user tiers; manage sources/tags.

### Out of scope

* Payments, SSO, non-RSS external APIs for MVP.
* Full article body storage from external sources.

---

## 3. Users & Tiers

* **anonymous:** can browse headlines; has limited full reads/day before signup.
* **free:** logged-in non-paying user; limited full reads/day.
* **standard:** logged-in user with higher daily limit; set via admin.
* **premium:** logged-in user with unlimited reads; set via admin.

> New signups default to  **free** .

---

## 4. Functional Requirements

### 4.1 Configuration (YAML as source of truth)

* Must define:
  * **App:** site name, timezone (`America/Chicago`).
  * **Content:** RSS feeds; refresh TTL; lazy-refresh toggle.
  * **Taxonomy:** small allow-list of categories; auto-tag from feed keywords.
  * **Search:** fields (`title`, `summary`) and basic mode.
  * **UI:** banner/CTA texts; counter visibility.
  * **Tiers:** per-tier settings for:
    * Page access: `headlines`, `detail`, `search` (enabled/disabled).
    * Content level per page: `headline | summary | detail`.
    * Metering: `applies`, `reads_per_day`, `count_scope` (detail only).
    * Content rules: allowed categories/sources; snippet length.
    * UI flags (show reads-left, per-tier CTA text).
* **Load on server start** .
* **Manual reload only** via a **superuser-only** endpoint; on invalid YAML, keep last good config.

### 4.2 Ingestion

* **Command:** `ingest_news` fetches/normalizes RSS items into the DB.
* **Dedup:** compute a stable hash (based on canonical link/fallbacks) and upsert.
* **Timeouts:** per-feed timeouts; skip slow feeds.
* **Refresh policy:**
  * Show content immediately.
  * If stale (`> TTL`), optionally trigger a **non-blocking** lazy refresh; avoid concurrent runs with a simple lock.
  * Show a small “stale” indicator when beyond TTL.

### 4.3 Content model & display

* Store  **title, summary/snippet, link (URL), source, published time** , optional image, tags/keywords.
* **External content** is shown as **snippet + link-out** on the detail page (no full body).
* **Headlines page** shows content per tier’s `content_level` (e.g., `headline` for anonymous; `summary` for others).

### 4.4 Metering & gating

* **Count only on the Detail page** (per `count_scope = "detail"`).
* **anonymous:** best-effort daily counter via  **signed cookie** ; resets at local midnight.
* **free/standard:** daily counter via DB (`ReadEvent`); unique per `(user, article, date)` to avoid double counts.
* **premium:** metering disabled.
* **Soft wall:** when `reads_today >= reads_per_day`, show a single wall page with per-tier CTA text from YAML.
* **Reads-left counter** visible when enabled in YAML.

### 4.5 Search

* Query param `q`; `icontains` over YAML-listed fields (title, summary).
* Return most recent results, capped (e.g., top 50).

### 4.6 Admin

* All teammates are  **superusers** .
* Admin can:
  * Toggle user tier ( **free/standard/premium** ).
  * Enable/disable RSS sources.
  * Edit article tags/categories if needed.
  * Trigger **Reload Config** (validates; keeps last good config on failure).

---

## 5. Non-Functional Requirements

* **Simplicity:** one Django app; no background workers/services.
* **Cost:** $0 (RSS sources; SQLite).
* **Reliability:**
  * On YAML error, retain last valid config and display an admin warning.
  * On ingestion issues, serve last stored articles; skip failing feeds.
* **Timezone:** all metering uses **America/Chicago** day boundaries.
* **Licensing:** only store headline/snippet/link from external feeds.

---

## 6. Data Requirements (entities & key fields)

* **Source:** `name`, `type="rss"`, `url`, `enabled`.
* **Article:** `source_id`, `title`, `url`, `summary`, `image_url?`, `published_at`, `keywords (text/json)`, `tags (text/json)`, `hash (unique)`.
* **User:** Django auth user.
* **UserProfile:** `user_id (1:1)`, `tier ∈ {"free","standard","premium"}` (default `free`).
* **ReadEvent:** `user_id`, `article_id`, `date` (local date); unique on `(user, article, date)`.

---

## 7. Page/Endpoint Requirements

* **GET /** — Headlines
  * Enforce page enablement.
  * Filter by allowed categories/sources if configured.
  * Render per-tier `content_level`.
  * Show reads-left counter and tier hints per YAML.
* **GET /a/** — Detail
  * Enforce page enablement.
  * Apply metering (cookie or DB).
  * On limit, show soft wall; else render snippet + link-out.
* **GET /search?q=** — Search
  * `icontains` over configured fields; cap results by recency.
* **GET /account** — Account
  * Show current tier and reads left today.
* **POST /admin/reload-config** — Superuser only
  * Reload YAML; success swaps config; failure keeps prior config and reports error.

---

## 8. Tier Defaults (configurable in YAML)

* **anonymous:** `reads_per_day = 3`
* **free:** `reads_per_day = 5`
* **standard:** `reads_per_day = 11`
* **premium:** unlimited (metering off)
* **Headlines content level:** `anonymous = headline`, others = `summary`.
* **Detail page:** enabled for all tiers; shows snippet + link-out.

---

## 9. Acceptance Criteria (MVP)

* YAML controls  **tiers, page access, content levels, limits, UI text** ; manual reload works and validates.
* RSS ingestion populates articles; duplicates are avoided; slow feeds don’t block; stale indicator shown when beyond TTL.
* **Metering works exactly** :
* anonymous: 3 reads/day → soft wall at 4th; resets at local midnight.
* free: 5 reads/day → soft wall at 6th.
* standard: 11 reads/day → soft wall at 12th.
* premium: never soft-walled.
* Headlines, Detail, Search, Account pages render per tier rules; reads-left counter displays when enabled.
* Admin can set user tiers and reload config.
* Works locally on **SQLite** for the class demo.
