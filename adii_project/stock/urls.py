from django.urls import path
from . import views

urlpatterns = [
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/ajouter/', views.stock_edit, name='stock_add'),
    path('stock/modifier/<int:pk>/', views.stock_edit, name='stock_edit'),
    path('stock/mouvement/<int:pk>/', views.stock_movement, name='stock_movement'),
    path('stock/mouvements/', views.stock_movements_all, name='stock_movements_all'),
]