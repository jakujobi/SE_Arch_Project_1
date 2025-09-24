## `venv` setup (one-time)

* Create & activate
  * macOS/Linux:
    * `python3 -m venv .venv`
    * `source .venv/bin/activate`
  * Windows (PowerShell):
    * `py -3 -m venv .venv`
    * `.venv\Scripts\Activate.ps1`
* Install deps
  * `pip install -r requirements.txt`
* Freeze (for reproducibility)
  * `pip freeze > requirements-lock.txt`




# **Environment**

* Create venv: `py -3.13 -m venv .venv`
* Activate (PowerShell): `. .\.venv\Scripts\Activate.ps1`
* Install deps: `python -m pip install -r requirements.txt`


## **DB & admin**

* Make migrations: `python manage.py makemigrations`
* Apply migrations: `python manage.py migrate`
* Create superuser: `python manage.py createsuperuser`
* Seed demo users: `python manage.py seed_demo`


## **Ingestion**

* Run RSS ingest: `python manage.py ingest_news`


## **Run app**

* Dev server: `python manage.py runserver`
* Alt port: `python manage.py runserver 8080`


## **Tests**

* Run tests: `python manage.py test`
