from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'nom', 'prenom', 'matricule', 'service', 'role']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations ADII', {'fields': ('role', 'matricule', 'service', 'nom', 'prenom')}),
    )
