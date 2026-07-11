# Developer guide

## Requirements

- Python 3.10+
- PostgreSQL 15+
- pip

## Database setup

The app expects PostgreSQL on **port 5433** (not the default 5432).

### Linux (Ubuntu/Debian)

```bash
sudo apt install postgresql postgresql-client libpq-dev
sudo systemctl start postgresql

# If you want to keep the default 5432 port, change settings.py:
#   'PORT': '5433' → 'PORT': '5432'
# Or configure PostgreSQL to listen on 5433:
#   sudo sed -i 's/port = 5432/port = 5433/' /etc/postgresql/*/main/postgresql.conf
#   sudo systemctl restart postgresql

sudo -u postgres psql -c "CREATE DATABASE adii_db;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'admin';"
```

### Windows

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. During installation, set:
   - **Port**: 5433 (or note your port and update `settings.py`)
   - **Password**: `admin`
3. Open **SQL Shell (psql)** and run:
   ```sql
   CREATE DATABASE adii_db;
   ```
4. Or use pgAdmin:
   - Right-click **Databases** → **Create** → **Database**
   - Name: `adii_db`

### macOS

```bash
brew install postgresql@15
brew services start postgresql@15

# Edit port to 5433 (default is 5432):
#   sed -i '' 's/port = 5432/port = 5433/' /opt/homebrew/var/postgresql@15/postgresql.conf
#   brew services restart postgresql@15

createdb adii_db
psql -c "ALTER USER postgres PASSWORD 'admin';"
```

### Using different port / password

If you already have PostgreSQL running on port 5432 or use a different password, edit `settings.py`:

```python
'PORT': '5432',      # your port
'PASSWORD': 'your_password',
```

## Project setup

```bash
# Clone and enter the project
git clone <repo-url>
cd adii_project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env          # optional — defaults are fine

# Run migrations and seed data
python manage.py migrate
python manage.py populate_db

# Start development server
python manage.py runserver
```

Open http://127.0.0.1:8000

## Project structure

```
.
├── accounts/          # Auth, profiles, roles
│   ├── models.py      # Custom User model
│   ├── views.py       # Login, register, profile
│   └── management/    # populate_db command
├── measurements/      # Measurement forms & workflow
│   ├── models.py      # Measurement, RetourEffet
│   └── views.py       # Role-based dashboards
├── stock/             # Stock & movements
├── notifications/     # Notifications & emails
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── settings.py        # Django settings
└── urls.py            # Root URL config
```

## Commands

| Task | Command |
|------|---------|
| Run dev server | `python manage.py runserver` |
| Create migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Seed demo data | `python manage.py populate_db` |
| Django shell | `python manage.py shell` |
| Collect static | `python manage.py collectstatic` |

## Admin interface

Access the Django admin at `/admin/` with the admin demo account.

## Email

Emails print to the console by default. To use SendGrid or SMTP, configure your credentials in `.env` (see `.env.example`).
