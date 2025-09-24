# Role-Based News App (SE_Arch_Project_1)

This project is a Django-based news aggregator developed for a software architecture class (SE340). The core objective is to implement a role-based news application that serves content from RSS feeds to different tiers of users with metered access.

## Project Overview

The application demonstrates the use of architectural patterns to manage complexity in a system with varying user permissions. It's designed to be simple, server-rendered, and run at zero cost using SQLite and public RSS feeds.

### Key Features

-   **Tiered User Access**: Four user roles (`anonymous`, `free`, `standard`, `premium`) with different daily reading limits.
-   **Metered Paywall**: A "soft wall" that limits access to full article details once a user's daily quota is reached.
-   **RSS Ingestion**: A management command to fetch, normalize, and store news articles from a configurable list of RSS feeds.
-   **Django Admin Integration**: Superusers can manage user tiers and news sources through the Django admin interface.
-   **Configuration-driven**: Core settings like reading limits and feed URLs are managed in `settings.py`.

## Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

-   Python 3.x
-   Pip

### Setup

1.  **Clone the repository:**
    ```sh
    git clone <repository-url>
    cd SE_Arch_Project_1
    ```

2.  **Create and activate a virtual environment:**

    *   On Windows (PowerShell):
        ```sh
        py -3 -m venv .venv
        .venv\Scripts\Activate.ps1
        ```
    *   On macOS/Linux:
        ```sh
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run database migrations:**
    ```sh
    python manage.py migrate
    ```

5.  **Create a superuser to access the admin panel:**
    ```sh
    python manage.py createsuperuser
    ```

### Running the Development Server

Once the setup is complete, you can start the Django development server:

```sh
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`. The admin panel is at `http://127.0.0.1:8000/admin/`.

## Project Status

For a detailed list of changes and completed work, please see the [Changelog](docs/changelog.md).