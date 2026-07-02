from django.urls import path
from . import views
urlpatterns = [
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/lire/<int:pk>/', views.mark_read, name='mark_read'),
    path('notifications/tout-lire/', views.mark_all_read, name='mark_all_read'),
]
