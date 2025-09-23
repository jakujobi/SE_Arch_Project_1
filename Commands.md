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
