<p align="right">
  <a href="README.md">🇫🇷 Français</a>
</p>

<a href="#">
  <p align="center">
    <img src="https://github.com/Axmae/adii_project/blob/main/ADII_HEADER_README.svg" alt="ADII Header">
  </p>
</a>
<h2 align="center">ADII — Garment Management</h2>
<p align="center">Web application for managing measurement forms and garment stock for the Customs and Indirect Taxes Administration.</p>
<br/>

## Features

- 👥 **3 separate workspaces** — Agent, Administrator, Technician
- 📋 **Full workflow** — pending → validated → in_production → ready → delivered
- 📦 **Stock management** with low-threshold alerts
- 🔔 **Real-time notifications**
- 👤 **Profiles & roles** managed by the admin
- 🎨 **Role-adapted interface**

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open **http://127.0.0.1:8000**

## Quick Start

1. **Log in** — Use one of the demo accounts
2. **Create a form** — Fill in an agent's measurements
3. **Track status** — The workflow goes through 5 stages
4. **Manage stock** — View and update inventory

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Administrator | admin@adii.ma | Admin2026! |
| Technician | tech@adii.ma | Tech2026! |
| Agent | agent@adii.ma | Agent2026! |
| Secretary | secretaire@adii.ma | Secretaire2026! |

## Project Structure

```
.
├── accounts/          # Users, auth, roles
├── measurements/      # Measurement forms, workflow
├── stock/             # Stock management
├── notifications/     # Notification system
├── templates/         # Role-based HTML templates
├── static/            # CSS, JS, images
├── settings.py        # Django configuration
├── urls.py            # Main routing
├── manage.py          # CLI entry point
└── requirements.txt   # Dependencies
```

## Troubleshooting

**Login issues?**  
Check that the server is running and use the correct credentials.

**Django commands?**  
Use `python manage.py help` to list all available commands.
