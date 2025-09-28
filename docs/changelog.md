# Changelog

All notable changes to this project will be documented in this file.
This project follows a simple **Added/Changed/Fixed/Removed** format.

## [Unreleased]

### Added

- **User Authentication & Profile App (`Profile`)**
  - Created a new Django app, `Profile`, to handle all user-related functionality.
  - Implemented user registration, login, and logout views.
  - Added profile viewing and editing capabilities.
  - *Contributor: Draix Wyatt*
- **Subscription & Payment Models**
  - Added `Subscription` and `Payment` models to the `Profile` app, extending the project beyond the MVP to support time-based subscriptions.
  - Created a payment view to simulate purchasing or extending a subscription.
  - *Contributor: Draix Wyatt*
- **News Ingestion Management Command (`ingest_news`)**
  - Created a robust, idempotent management command (`ingest_news`) within the `news` app to fetch articles from RSS feeds.
  - Implemented a file-based lock to prevent concurrent runs, ensuring safe execution.
  - Added logic to automatically seed the `Source` table from the `FEEDS` list in `settings.py`.
  - Built-in error handling to gracefully skip failing feeds without crashing the entire process.
  - *Contributor: John Akujobi*

### Database / Migrations

- Created initial migrations for the `Profile` app to create the `Profile`, `Subscription`, and `Payment` tables.

## [0.1.0] - 2025-09-23 — Bootstrap models, admin, and settings

Contributor: John Akujobi

### Added

- **Django app `news`** wired into project via `news.apps.NewsConfig`.
- **Data model** (SQLite-friendly):
  - `Source`: external feed/source registry (enable/disable).
  - `Article`: normalized item with summary/snippet, image URL, timestamps, tags/keywords (JSON stored as TEXT), and **dedup `hash`**.
  - `UserProfile`: 1:1 with user; holds **tier** (`free|standard|premium`).
  - `ReadEvent`: per-day metering for logged-in users with **UNIQUE (user, article, date)**.
- **Signals**: auto-create `UserProfile(tier="free")` on user creation.
- **Admin**:
  - List, search, and filter for `Source`, `Article`, `ReadEvent`, `UserProfile`.
  - Tier bulk actions (set FREE/STANDARD/PREMIUM).
  - Inline `UserProfile` on Django User admin.
- **Settings** additions:
  - `TIME_ZONE="America/Chicago"` (local day boundary for metering).
  - **Feeds** list (`FEEDS`) seeded with 5 tech RSS URLs.
  - Metering/refresh knobs in code:`ANON_READS_PER_DAY=3`, `FREE_READS_PER_DAY=5`, `STANDARD_READS_PER_DAY=11`,`TTL_MINUTES=10`, `LAZY_REFRESH=True`,plus `FETCH_TIMEOUT_SECONDS=5`, `MAX_SEARCH_RESULTS=50`.
  - Minimal `TIER_CONFIG` for headlines content level per tier.

### Changed

- `INSTALLED_APPS`: added `news.apps.NewsConfig`.

### Fixed

- n/a

### Removed

- n/a

### Database / Migrations

- Created `news/migrations/0001_initial.py`
  - Tables: `source`, `article`, `userprofile`, `readevent`.
  - Indexes: `idx_article_pub_desc` (`-published_at`), `idx_article_title` (`title`).
  - Constraint: `uq_read_once_per_day` on `(user, article, date)`.

## [0.0.1] 2025-09-23

### Added

- **Project Initialization & Setup**
  - Reviewed project requirements and proposal to establish a clear understanding of the MVP.
  - Set up the initial Django project structure with `ragtagnews` project and `news` app.
  - Created and activated a Python virtual environment to manage dependencies.
  - *Contributor: John Akujobi*
