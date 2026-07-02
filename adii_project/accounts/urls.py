from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
]
