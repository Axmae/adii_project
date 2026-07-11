from django.urls import path
from . import views

urlpatterns = [
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/nouvelle/', views.create_measurement, name='create_measurement'),
    path('agent/modifier/<int:pk>/', views.edit_measurement, name='edit_measurement'),
    path('agent/retour/', views.enregistrer_retour, name='enregistrer_retour'),
    path('secretaire/', views.secretaire_dashboard, name='secretaire_dashboard'),
    path('secretaire/nouvelle/', views.secretaire_create, name='secretaire_create'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/valider/<int:pk>/', views.validate_measurement, name='validate_measurement'),
    path('admin-dashboard/utilisateurs/', views.manage_users, name='manage_users'),
    path('admin-dashboard/utilisateurs/<int:user_id>/role/', views.change_role, name='change_role'),
    path('admin-dashboard/livraison-groupee/', views.livraison_groupee, name='livraison_groupee'),
    path('admin-dashboard/livraison-groupee/confirmer/', views.confirmer_livraison_groupee, name='confirmer_livraison_groupee'),
    path('admin-dashboard/livraison-groupee/reception/', views.reception_pdf, name='reception_pdf'),
    path('admin-dashboard/avancement-groupe/', views.avancement_groupe, name='avancement_groupe'),
    path('admin-dashboard/avancement-groupe/confirmer/', views.confirmer_avancement_groupe, name='confirmer_avancement_groupe'),
    path('admin-dashboard/historique/', views.historique_agents, name='historique_agents'),
    path('admin-dashboard/historique/excel/', views.export_historique_excel, name='export_historique_excel'),
    path('admin-dashboard/historique/pdf/', views.export_historique_pdf, name='export_historique_pdf'),
    path('technicien/', views.tech_dashboard, name='tech_dashboard'),
    path('technicien/statut/<int:pk>/', views.update_status, name='update_status'),
    path('dossier/<int:pk>/', views.measurement_detail, name='measurement_detail'),
]