from django.contrib import admin
from .models import StockItem

@admin.register(StockItem)
class StockAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'size', 'quantity', 'min_threshold', 'is_low']
    list_filter = ['category', 'size']
