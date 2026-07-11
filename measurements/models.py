from django.db import models
from django.conf import settings


class RetourEffet(models.Model):
    MOTIF_CHOICES = [
        ('destruction', 'Destruction'),
        ('perte', 'Perte'),
        ('usure', 'Usure normale'),
        ('autre', 'Autre'),
    ]
    TYPE_CHOICES = [
        ('uniforme_ete', 'Uniforme été'),
        ('uniforme_hiver', 'Uniforme hiver'),
        ('veste', 'Veste'),
        ('pantalon', 'Pantalon'),
        ('chemise', 'Chemise'),
        ('complet', 'Tenue complète'),
    ]

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retours'
    )
    type_equipement = models.CharField(max_length=50, choices=TYPE_CHOICES)
    quantite = models.IntegerField()
    motif = models.CharField(max_length=20, choices=MOTIF_CHOICES, default='destruction')
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='retours_enregistres'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Retour d'effet"
        verbose_name_plural = "Retours d'effets"

    def __str__(self):
        return f"{self.agent.get_full_name()} — {self.get_type_equipement_display()} x{self.quantite} ({self.get_motif_display()})"


class Measurement(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('en_production', 'En production'),
        ('pret', 'Prêt'),
        ('livre', 'Livré'),
        ('refuse', 'Refusé'),
    ]
    TYPE_CHOICES = [
        ('uniforme_ete', 'Uniforme été'),
        ('uniforme_hiver', 'Uniforme hiver'),
        ('veste', 'Veste'),
        ('pantalon', 'Pantalon'),
        ('chemise', 'Chemise'),
        ('complet', 'Tenue complète'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    rempli_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fiches_remplies',
        verbose_name='Rempli par'
    )
    type_equipement = models.CharField(max_length=50, choices=TYPE_CHOICES)
    tour_poitrine = models.FloatField(verbose_name='Tour de poitrine (cm)')
    tour_taille = models.FloatField(verbose_name='Tour de taille (cm)')
    tour_hanches = models.FloatField(verbose_name='Tour de hanches (cm)')
    epaules = models.FloatField(verbose_name='Largeur épaules (cm)')
    manche = models.FloatField(verbose_name='Longueur manche (cm)')
    entrejambe = models.FloatField(verbose_name='Entrejambe (cm)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    notes_admin = models.TextField(blank=True, verbose_name='Notes admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fiche de mesure'
        verbose_name_plural = 'Fiches de mesure'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_type_equipement_display()} ({self.get_status_display()})"

    def status_color(self):
        colors = {
            'en_attente': 'amber',
            'valide': 'blue',
            'en_production': 'purple',
            'pret': 'teal',
            'livre': 'green',
            'refuse': 'red',
        }
        return colors.get(self.status, 'gray')

    def can_edit(self):
        return self.status == 'en_attente'