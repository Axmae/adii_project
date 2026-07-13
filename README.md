<p align="right">
  <a href="README.en.md">EN</a>
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
<h2 align="center">ADII — Gestion d'habillement</h2>
<p align="center">Application web Django pour la gestion des fiches de mesure et du stock d'habillement (Administration des Douanes et Impôts Indirects).</p>
<br/>

## Fonctionnalités

- **4 espaces** : Agent, Administrateur, Technicien, Secrétaire
- **Workflow** : en_attente → validé → en_production → prêt → livré
- **Stock** avec alertes seuil bas
- **Notifications** en temps réel
- **Rôles** gérés par l'admin

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_db
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000

## Configuration

**Base de donnees** : PostgreSQL sur **port 5433** (pas le 5432 par defaut).  
Modifier le port dans `settings.py` ligne 67 si besoin :

```python
'PORT': '5433',   # changez ici si votre PostgreSQL utilise 5432
```

Pour le reste (installation PostgreSQL, creation de la DB), voir [DEVELOPER.md](DEVELOPER.md).

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Administrateur | admin@adii.ma | Admin2026! |
| Technicien | tech@adii.ma | Tech2026! |
| Agent | agent@adii.ma | Agent2026! |
| Secrétaire | secretaire@adii.ma | Secretaire2026! |

## Structure

```
.
├── accounts/          # Auth, profils, rôles
├── measurements/      # Fiches de mesure, workflow
├── stock/             # Gestion du stock
├── notifications/     # Notifications, emails
├── templates/         # HTML par rôle
├── static/            # CSS, JS, images
├── settings.py
├── urls.py
├── manage.py
├── requirements.txt
└── .env.example
```
