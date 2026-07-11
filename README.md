# ADII — Gestion d'habillement (Django)

Réplique complète de https://adii-garment-buddy.lovable.app avec Django.

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Administrateur | admin@adii.ma | Admin2026! |
| Technicien | tech@adii.ma | Tech2026! |
| Agent | agent@adii.ma | Agent2026! |

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Puis ouvrir http://127.0.0.1:8000

## Structure

```
.
├── accounts/          # Utilisateurs, auth, rôles
├── measurements/      # Fiches de mesure, workflow
├── stock/             # Gestion du stock
├── notifications/     # Système de notifications
├── templates/         # Templates HTML par rôle
├── static/            # CSS, JS, images
├── settings.py        # Configuration Django
├── urls.py            # Routage principal
├── manage.py          # Point d'entrée CLI
└── requirements.txt   # Dépendances
```

## Fonctionnalités

- **3 espaces distincts** : Agent, Administrateur, Technicien
- **Workflow complet** : en_attente → validé → en_production → prêt → livré
- **Gestion du stock** avec alertes seuil bas
- **Notifications** en temps réel (sans WebSocket — polling-ready)
- **Gestion des rôles** par l'admin
- **Interface Django Admin** sur /admin/
