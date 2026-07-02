from django.contrib import admin
from .models import Measurement

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['user', 'type_equipement', 'status', 'created_at']
    list_filter = ['status', 'type_equipement']
    search_fields = ['user__nom', 'user__prenom', 'user__matricule']
