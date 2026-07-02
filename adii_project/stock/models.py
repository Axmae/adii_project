from django.db import models
from django.conf import settings

class StockItem(models.Model):
    CATEGORY_CHOICES = [
        ('uniforme_ete', 'Uniforme été'),
        ('uniforme_hiver', 'Uniforme hiver'),
        ('veste', 'Veste'),
        ('pantalon', 'Pantalon'),
        ('chemise', 'Chemise'),
        ('complet', 'Tenue complète'),
    ]
    SIZE_CHOICES = [
        ('XS','XS'),('S','S'),('M','M'),('L','L'),
        ('XL','XL'),('XXL','XXL'),('XXXL','XXXL')
    ]

    name = models.CharField(max_length=100, verbose_name='Nom')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    quantity = models.IntegerField(default=0)
    min_threshold = models.IntegerField(default=5, verbose_name='Seuil minimum')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'size']
        verbose_name = 'Article en stock'
        verbose_name_plural = 'Stock'

    def __str__(self):
        return f"{self.name} — {self.size} ({self.quantity})"

    def is_low(self):
        return self.quantity < self.min_threshold

    def status_label(self):
        if self.quantity == 0:
            return ('Épuisé', 'red')
        elif self.is_low():
            return ('Stock bas', 'amber')
        return ('Disponible', 'green')


class StockMovement(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    REASON_CHOICES = [
        ('livraison_fournisseur', 'Livraison fournisseur'),
        ('retour',               'Retour article'),
        ('production',           'Mise en production'),
        ('perte',                'Perte / Détérioration'),
        ('inventaire',           'Correction inventaire'),
        ('autre',                'Autre'),
    ]

    stock_item  = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    type        = models.CharField(max_length=10, choices=TYPE_CHOICES)
    reason      = models.CharField(max_length=40, choices=REASON_CHOICES)
    quantity    = models.IntegerField(verbose_name='Quantité')
    quantity_before = models.IntegerField(verbose_name='Qté avant')
    quantity_after  = models.IntegerField(verbose_name='Qté après')
    note        = models.TextField(blank=True, verbose_name='Note')
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'

    def __str__(self):
        return f"{self.get_type_display()} — {self.stock_item.name} ({self.quantity})"