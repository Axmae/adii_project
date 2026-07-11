<p align="right">
  <a href="README.en.md">English</a>
</p>

# ADII — Gestion d'habillement

Application web Django pour la gestion des fiches de mesure et du stock d'habillement (Administration des Douanes et Impôts Indirects).

---

## Fonctionnalités

- **3 espaces** : Agent, Administrateur, Technicien, Secrétaire
- **Workflow** : en_attente → validé → en_production → prêt → livré
- **Stock** avec alertes seuil bas
- **Notifications** en temps réel
- **Rôles** gérés par l'admin

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000

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
