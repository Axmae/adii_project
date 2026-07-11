from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from .models import StockItem, StockMovement
from notifications.utils import create_notification
from django import forms

class StockForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ['name', 'category', 'size', 'quantity', 'min_threshold']
        widgets = {
            'name':          forms.TextInput(attrs={'class': 'form-input'}),
            'category':      forms.Select(attrs={'class': 'form-input'}),
            'size':          forms.Select(attrs={'class': 'form-input'}),
            'quantity':      forms.NumberInput(attrs={'class': 'form-input'}),
            'min_threshold': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class MovementForm(forms.Form):
    type = forms.ChoiceField(
        choices=[('entree', 'Entrée ↑'), ('sortie', 'Sortie ↓')],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    reason = forms.ChoiceField(
        choices=StockMovement.REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Quantité'})
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Note optionnelle...'})
    )

def role_required_tech_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['technicien', 'admin']:
            messages.error(request, "Accès non autorisé.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

@role_required_tech_admin
def stock_list(request):
    items = StockItem.objects.all()
    # Stats globales
    total_items    = items.count()
    total_quantity = items.aggregate(t=Sum('quantity'))['t'] or 0
    low_stock      = items.filter(quantity__lt=models.F('min_threshold')).count()
    out_of_stock   = items.filter(quantity=0).count()
    # Derniers mouvements
    recent_movements = StockMovement.objects.select_related('stock_item', 'created_by').all()[:10]
    return render(request, 'technicien/stock.html', {
        'items': items,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'recent_movements': recent_movements,
    })

@role_required_tech_admin
def stock_edit(request, pk=None):
    item = get_object_or_404(StockItem, pk=pk) if pk else None
    if request.method == 'POST':
        form = StockForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Article mis à jour.")
            return redirect('stock_list')
    else:
        form = StockForm(instance=item)
    return render(request, 'technicien/stock_form.html', {'form': form, 'item': item})

@role_required_tech_admin
def stock_movement(request, pk):
    item = get_object_or_404(StockItem, pk=pk)
    if request.method == 'POST':
        form = MovementForm(request.POST)
        if form.is_valid():
            mvt_type  = form.cleaned_data['type']
            qty       = form.cleaned_data['quantity']
            reason    = form.cleaned_data['reason']
            note      = form.cleaned_data['note']
            qty_before = item.quantity

            if mvt_type == 'entree':
                item.quantity += qty
            else:
                if qty > item.quantity:
                    messages.error(request, f"Stock insuffisant. Disponible : {item.quantity}")
                    return redirect('stock_movement', pk=pk)
                item.quantity -= qty

            item.save()

            # Enregistrer le mouvement
            StockMovement.objects.create(
                stock_item=item,
                type=mvt_type,
                reason=reason,
                quantity=qty,
                quantity_before=qty_before,
                quantity_after=item.quantity,
                note=note,
                created_by=request.user,
            )

            # Notifier les admins si stock bas
            if item.is_low():
                from accounts.models import User
                for admin in User.objects.filter(role='admin'):
                    create_notification(
                        admin,
                        '⚠️ Stock bas',
                        f"{item.name} ({item.size}) : {item.quantity} unités restantes (seuil : {item.min_threshold}).",
                        category='stock'
                    )

            action = "Entrée" if mvt_type == 'entree' else "Sortie"
            messages.success(request, f"{action} de {qty} unité(s) enregistrée pour {item.name} ({item.size}).")
            return redirect('stock_list')
    else:
        form = MovementForm()

    movements = StockMovement.objects.filter(stock_item=item).select_related('created_by')[:20]
    return render(request, 'technicien/stock_movement.html', {
        'item': item,
        'form': form,
        'movements': movements,
    })

@role_required_tech_admin
def stock_movements_all(request):
    movements = StockMovement.objects.select_related('stock_item', 'created_by').all()
    # Filtres
    mvt_type = request.GET.get('type', '')
    search   = request.GET.get('search', '')
    if mvt_type:
        movements = movements.filter(type=mvt_type)
    if search:
        movements = movements.filter(
            Q(stock_item__name__icontains=search) |
            Q(note__icontains=search)
        )
    return render(request, 'technicien/stock_movements_all.html', {
        'movements': movements,
        'mvt_type': mvt_type,
        'search': search,
    })

# Nécessaire pour le filtre F()
from django.db import models