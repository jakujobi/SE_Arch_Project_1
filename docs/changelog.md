# Changelog

All notable changes to this project will be documented in this file.
This project follows a simple **Added/Changed/Fixed/Removed** format.

## [0.3.0] - 2025-09-29 — Full Content Ingestion

### Added
- **Full Content Storage**: Added a `content` field to the `Article` model in `news/models.py` to store the full HTML content of articles.
- **Content-Aware Ingestion**: The `ingest_news` management command now intelligently checks RSS feeds for full article content (often in a `content` field) and saves it. If full content is not available, it gracefully falls back to using the article summary.

### Changed
- **Article Detail View**: The article detail template (`article_detail.html`) now prioritizes displaying the full `content` if it exists, otherwise it will show the `summary`. This provides a richer reading experience when full content is available.

### Database / Migrations
- Created `news/migrations/0003_article_content.py` to add the new `content` column to the `news_article` table.

## [0.2.0] - 2025-09-28 — Content Display Implementation

Contributor: John Akujobi

### Added

- **Architectural Tier Bridge**: Implemented the `get_current_tier()` method on the `Profile` model. This creates a clean, decoupled interface between the `Profile` app's subscription logic and the `news` app's content display logic.
- **Dynamic Headlines Page**:
    - The main `home_view` now fetches and displays articles from the database.
    - Content is **tier-aware**: anonymous users see headlines only, while authenticated users see summaries.
    - Implemented a paginator to display 15 articles per page for better performance.
- **Article Detail Page**:
    - Created a new `article_detail_view` with a corresponding URL (`/article/<id>/`) and template to display individual articles.
    - The headlines page now correctly links to each article's detail page.
- **Improved UI**: Updated the headlines page to a more visually appealing grid layout that includes article thumbnails.

### Changed

- Refactored the project's URL configuration to use `include('news.urls')`, following Django best practices for app-specific URLs.
- Reorganized app-specific templates into subdirectories (e.g., `news/templates/news/`) to prevent name collisions and fix `TemplateDoesNotExist` errors.

### Fixed

- **Database Migrations**: Resolved an `OperationalError: no such table` by running the necessary `makemigrations` and `migrate` commands for the `Profile` app.
- **Template Paths**: Corrected template loading errors by adjusting template paths in the views to match the new directory structure.

## [0.1.5] - 2025-09-28 — User Management & Content Ingestion

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
