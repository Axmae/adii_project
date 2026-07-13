<p align="right">
  <a href="README.md">FR</a>
</p>

<a href="#">
  <p align="center">
    <img src="https://github.com/Axmae/adii_project/blob/main/ADII_HEADER_README.svg" alt="ADII Header">
  </p>
</a>
<a href="#">
  <p align="center">
    <img src="ADII_HEADER_README.svg" alt="ADII Header">
  </p>
</a>
<h2 align="center">ADII — Garment Management</h2>
<p align="center">Web application for managing measurement forms and garment stock for the Customs and Indirect Taxes Administration.</p>
<br/>

## Features

- **4 workspaces**: Agent, Administrator, Technician, Secretary
- **Workflow**: pending → validated → in_production → ready → delivered
- **Stock management** with low-stock alerts
- **Real-time notifications**
- **Role-based access**

## Quick start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_db
python manage.py runserver
```

Open http://127.0.0.1:8000

## Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Administrator | admin@adii.ma | Admin2026! |
| Technician | tech@adii.ma | Tech2026! |
| Agent | agent@adii.ma | Agent2026! |
| Secretary | secretaire@adii.ma | Secretaire2026! |

## Setup

**Database** : PostgreSQL on **port 5433** (not the default 5432).  
Change the port in `settings.py` line 67 if needed:

```python
'PORT': '5433',   # change this if your PostgreSQL uses 5432
```

For PostgreSQL installation and DB creation, see [DEVELOPER.md](DEVELOPER.md).
