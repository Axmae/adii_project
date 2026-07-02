from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('agent', 'Agent'),
        ('admin', 'Administrateur'),
        ('technicien', 'Technicien'),
        ('secretaire', 'Secrétaire'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    matricule = models.CharField(max_length=50, blank=True)
    service = models.CharField(max_length=100, blank=True)
    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)

    def is_admin(self):
        return self.role == 'admin'

    def is_technicien(self):
        return self.role == 'technicien'

    def is_agent(self):
        return self.role == 'agent'

    def is_secretaire(self):
        return self.role == 'secretaire'

    def get_full_name(self):
        return f"{self.prenom} {self.nom}".strip() or self.username

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'