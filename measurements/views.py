import io
import urllib.parse

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Count
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Measurement, RetourEffet
from .forms import MeasurementForm, AdminNoteForm, RetourEffetForm
from notifications.utils import create_notification
from notifications.email_utils import send_status_email
from stock.models import StockItem, StockMovement

def role_required(roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('auth')
            if request.user.role not in roles:
                messages.error(request, "Accès non autorisé.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# ─── AGENT ───────────────────────────────────────────────
@login_required
def agent_dashboard(request):
    measurements = Measurement.objects.filter(user=request.user)
    retours = RetourEffet.objects.filter(agent=request.user)
    return render(request, 'agent/dashboard.html', {
        'measurements': measurements,
        'retours': retours,
    })

@login_required
def create_measurement(request):
    if request.user.role != 'agent':
        return redirect('home')
    existing = Measurement.objects.filter(
        user=request.user,
        status__in=['en_attente', 'valide', 'en_production', 'pret']
    ).exists()
    if existing:
        messages.warning(request, "Vous avez déjà une fiche en cours de traitement.")
        return redirect('agent_dashboard')
    if request.method == 'POST':
        form = MeasurementForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.user = request.user
            m.rempli_par = request.user
            m.save()
            send_status_email(m)
            from accounts.models import User
            for admin in User.objects.filter(role='admin'):
                create_notification(
                    admin,
                    'Nouvelle fiche de mesure',
                    f"{request.user.get_full_name()} a soumis une fiche pour {m.get_type_equipement_display()}.",
                    category='measurement'
                )
            messages.success(request, "Fiche créée avec succès !")
            return redirect('agent_dashboard')
    else:
        form = MeasurementForm()
    return render(request, 'agent/create_measurement.html', {'form': form})

@login_required
def edit_measurement(request, pk):
    m = get_object_or_404(Measurement, pk=pk, user=request.user)
    if not m.can_edit():
        messages.error(request, "Cette fiche ne peut plus être modifiée.")
        return redirect('agent_dashboard')
    if request.method == 'POST':
        form = MeasurementForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            messages.success(request, "Fiche mise à jour.")
            return redirect('agent_dashboard')
    else:
        form = MeasurementForm(instance=m)
    return render(request, 'agent/create_measurement.html', {'form': form, 'edit': True})

# ─── SECRÉTAIRE ──────────────────────────────────────────
@role_required(['secretaire', 'admin'])
def secretaire_dashboard(request):
    measurements = Measurement.objects.select_related('user', 'rempli_par').order_by('-created_at')
    return render(request, 'secretaire/dashboard.html', {
        'measurements': measurements,
    })

@role_required(['secretaire', 'admin'])
def secretaire_create(request):
    from accounts.models import User
    agents = User.objects.filter(role='agent').order_by('nom')
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        agent = get_object_or_404(User, pk=agent_id, role='agent')
        existing = Measurement.objects.filter(
            user=agent,
            status__in=['en_attente', 'valide', 'en_production', 'pret']
        ).exists()
        if existing:
            messages.warning(request, f"{agent.get_full_name()} a déjà une fiche en cours.")
            return redirect('secretaire_dashboard')
        form = MeasurementForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.user = agent
            m.rempli_par = request.user
            m.save()
            send_status_email(m)
            for admin in User.objects.filter(role='admin'):
                create_notification(
                    admin,
                    'Nouvelle fiche de mesure',
                    f"Fiche de {agent.get_full_name()} remplie par {request.user.get_full_name()}.",
                    category='measurement'
                )
            messages.success(request, f"Fiche créée pour {agent.get_full_name()}.")
            return redirect('secretaire_dashboard')
    else:
        form = MeasurementForm()
    selected_agent = None
    agent_id = request.GET.get('agent')
    if agent_id:
        selected_agent = User.objects.filter(pk=agent_id, role='agent').first()
    return render(request, 'secretaire/create.html', {
        'form': form,
        'agents': agents,
        'selected_agent': selected_agent,
    })

# ─── ADMIN ───────────────────────────────────────────────
@role_required(['admin'])
def admin_dashboard(request):
    from accounts.models import User
    measurements = Measurement.objects.select_related('user').all()
    stats = {
        'total':         measurements.count(),
        'en_attente':    measurements.filter(status='en_attente').count(),
        'en_production': measurements.filter(status='en_production').count(),
        'pret':          measurements.filter(status='pret').count(),
        'livre':         measurements.filter(status='livre').count(),
        'agents':        User.objects.filter(role='agent').count(),
    }
    stock_alerts = StockItem.objects.filter(
        quantity__lt=F('min_threshold')
    ).order_by('quantity')
    recent_stock_movements = StockMovement.objects.select_related(
        'stock_item', 'created_by'
    ).all()[:8]
    return render(request, 'admin_panel/dashboard.html', {
        'measurements':           measurements,
        'stats':                  stats,
        'stock_alerts':           stock_alerts,
        'recent_stock_movements': recent_stock_movements,
    })

@role_required(['admin'])
def validate_measurement(request, pk):
    m = get_object_or_404(Measurement, pk=pk)
    action = request.POST.get('action')
    if action == 'valide':
        m.status = 'valide'
        m.save()
        send_status_email(m)
        from accounts.models import User
        for tech in User.objects.filter(role='technicien'):
            create_notification(
                tech,
                'Nouvelle fiche à traiter',
                f"La fiche de {m.user.get_full_name()} a été validée.",
                category='measurement'
            )
        create_notification(
            m.user,
            'Fiche validée',
            f"Votre demande pour {m.get_type_equipement_display()} a été validée.",
            category='measurement'
        )
        messages.success(request, "Fiche validée.")
    elif action == 'refuse':
        m.status = 'refuse'
        m.notes_admin = request.POST.get('notes_admin', '')
        m.save()
        send_status_email(m)
        create_notification(
            m.user,
            'Fiche refusée',
            f"Votre demande a été refusée. {m.notes_admin}",
            category='measurement'
        )
        messages.warning(request, "Fiche refusée.")
    return redirect('admin_dashboard')

@role_required(['admin'])
def manage_users(request):
    from accounts.models import User
    users = User.objects.all().order_by('role', 'nom')
    return render(request, 'admin_panel/users.html', {'users': users})

@role_required(['admin'])
def change_role(request, user_id):
    from accounts.models import User
    user = get_object_or_404(User, pk=user_id)
    new_role = request.POST.get('role')
    if new_role in ['agent', 'admin', 'technicien', 'secretaire']:
        user.role = new_role
        user.save()
        messages.success(request, f"Rôle de {user.get_full_name()} mis à jour.")
    return redirect('manage_users')

@role_required(['admin'])
def livraison_groupee(request):
    fiches_pretes = Measurement.objects.filter(
        status='pret'
    ).select_related('user').order_by('user__nom')
    return render(request, 'admin_panel/livraison_groupee.html', {
        'fiches_pretes': fiches_pretes,
    })

@role_required(['admin'])
def confirmer_livraison_groupee(request):
    if request.method == 'POST':
        ids = request.POST.getlist('fiche_ids')
        if not ids:
            messages.warning(request, "Aucune fiche sélectionnée.")
            return redirect('livraison_groupee')
        fiches = Measurement.objects.filter(pk__in=ids, status='pret')
        count = fiches.count()
        for fiche in fiches:
            fiche.status = 'livre'
            fiche.save()
            send_status_email(fiche)
            create_notification(
                fiche.user,
                'Tenue livrée ✅',
                f"Votre tenue ({fiche.get_type_equipement_display()}) vous a été remise officiellement.",
                category='measurement'
            )
        messages.success(request, f"{count} tenue(s) marquée(s) comme livrée(s).")
        return redirect('livraison_groupee')
    return redirect('livraison_groupee')

@role_required(['admin', 'secretaire'])
def avancement_groupe(request):
    from accounts.models import User
    fiches = Measurement.objects.filter(
        status__in=['en_attente', 'valide', 'en_production', 'pret']
    ).select_related('user', 'rempli_par').order_by('user__nom')
    agents = User.objects.filter(role='agent').order_by('nom')
    agent_filter  = request.GET.get('agent', '')
    status_filter = request.GET.get('status', '')
    if agent_filter:
        fiches = fiches.filter(user__pk=agent_filter)
    if status_filter:
        fiches = fiches.filter(status=status_filter)
    return render(request, 'admin_panel/avancement_groupe.html', {
        'fiches':         fiches,
        'agents':         agents,
        'agent_filter':   agent_filter,
        'status_filter':  status_filter,
        'status_choices': Measurement.STATUS_CHOICES,
    })

@role_required(['admin', 'secretaire'])
def confirmer_avancement_groupe(request):
    if request.method == 'POST':
        ids        = request.POST.getlist('fiche_ids')
        new_status = request.POST.get('new_status')
        valid_statuses = ['en_attente', 'valide', 'en_production', 'pret', 'livre', 'refuse']
        if not ids:
            messages.warning(request, "Aucune fiche sélectionnée.")
            return redirect('avancement_groupe')
        if new_status not in valid_statuses:
            messages.error(request, "Statut invalide.")
            return redirect('avancement_groupe')
        fiches = Measurement.objects.filter(pk__in=ids)
        count  = fiches.count()
        status_labels = {
            'en_attente':    'En attente',
            'valide':        'Validé',
            'en_production': 'En production',
            'pret':          'Prêt',
            'livre':         'Livré',
            'refuse':        'Refusé',
        }
        notif_msgs = {
            'valide':        "Votre fiche a été validée par le responsable.",
            'en_production': "Votre tenue est en cours de fabrication.",
            'pret':          "Votre tenue est prête ! Venez la récupérer.",
            'livre':         "Votre tenue vous a été remise officiellement.",
            'refuse':        "Votre demande a été refusée.",
            'en_attente':    "Votre fiche a été remise en attente.",
        }
        for fiche in fiches:
            fiche.status = new_status
            fiche.save()
            send_status_email(fiche)
            create_notification(
                fiche.user,
                f"Avancement mis à jour — {status_labels[new_status]}",
                notif_msgs.get(new_status, "Votre dossier a été mis à jour."),
                category='measurement'
            )
            if new_status == 'en_production':
                item = StockItem.objects.filter(category=fiche.type_equipement).first()
                if item and item.quantity > 0:
                    qty_before = item.quantity
                    item.quantity -= 1
                    item.save()
                    StockMovement.objects.create(
                        stock_item=item,
                        type='sortie',
                        reason='production',
                        quantity=1,
                        quantity_before=qty_before,
                        quantity_after=item.quantity,
                        note=f"Mise en production groupée — fiche #{fiche.pk} ({fiche.user.get_full_name()})",
                        created_by=request.user,
                    )
                    if item.quantity < item.min_threshold:
                        from accounts.models import User
                        for admin in User.objects.filter(role='admin'):
                            create_notification(
                                admin,
                                '⚠️ Stock bas',
                                f"{item.name} ({item.size}) : {item.quantity} unités restantes.",
                                category='stock'
                            )
        messages.success(request, f"{count} fiche(s) mise(s) à jour → {status_labels[new_status]}.")
        return redirect('avancement_groupe')
    return redirect('avancement_groupe')

# ─── TECHNICIEN ──────────────────────────────────────────
@role_required(['technicien'])
def tech_dashboard(request):
    measurements = Measurement.objects.filter(
        status__in=['valide', 'en_production', 'pret']
    ).select_related('user')
    return render(request, 'technicien/dashboard.html', {'measurements': measurements})

@role_required(['technicien'])
def update_status(request, pk):
    m = get_object_or_404(Measurement, pk=pk)
    new_status = request.POST.get('status')
    allowed = {
        'valide':        'en_production',
        'en_production': 'pret',
        'pret':          'livre',
    }
    if new_status == allowed.get(m.status):
        m.status = new_status
        m.save()
        send_status_email(m)
        if new_status == 'en_production':
            item = StockItem.objects.filter(category=m.type_equipement).first()
            if item and item.quantity > 0:
                qty_before = item.quantity
                item.quantity -= 1
                item.save()
                StockMovement.objects.create(
                    stock_item=item,
                    type='sortie',
                    reason='production',
                    quantity=1,
                    quantity_before=qty_before,
                    quantity_after=item.quantity,
                    note=f"Mise en production — fiche #{m.pk} ({m.user.get_full_name()})",
                    created_by=request.user,
                )
                if item.quantity < item.min_threshold:
                    from accounts.models import User
                    for admin in User.objects.filter(role='admin'):
                        create_notification(
                            admin,
                            '⚠️ Stock bas',
                            f"{item.name} ({item.size}) : {item.quantity} unités restantes (seuil : {item.min_threshold}).",
                            category='stock'
                        )
        msgs = {
            'en_production': "Votre équipement est en cours de fabrication.",
            'pret':          "Votre équipement est prêt ! Venez le récupérer.",
            'livre':         "Votre équipement vous a été remis.",
        }
        if new_status in msgs:
            create_notification(
                m.user,
                "Statut mis à jour",
                msgs[new_status],
                category='measurement'
            )
        messages.success(request, f"Statut mis à jour : {m.get_status_display()}")
    return redirect('tech_dashboard')

# ─── RETOUR D'EFFETS (Agent) ──────────────────────────────
@login_required
def enregistrer_retour(request):
    if request.user.role != 'agent':
        return redirect('home')
    if request.method == 'POST':
        form = RetourEffetForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.agent = request.user
            r.created_by = request.user
            r.save()
            from accounts.models import User
            for admin in User.objects.filter(role='admin'):
                create_notification(
                    admin,
                    'Retour d\'effet déclaré',
                    f"{request.user.get_full_name()} a retourné {r.quantite} x {r.get_type_equipement_display()} pour {r.get_motif_display()}.",
                    category='stock'
                )
            messages.success(request, "Retour enregistré avec succès.")
            return redirect('agent_dashboard')
    else:
        form = RetourEffetForm()
    return render(request, 'agent/retour.html', {'form': form})


# ─── HISTORIQUE PAR AGENT (Admin) ─────────────────────────
@role_required(['admin'])
def historique_agents(request):
    from accounts.models import User
    agents = User.objects.filter(role='agent').order_by('nom')
    agent_filter = request.GET.get('agent', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    if agent_filter:
        agents = agents.filter(pk=agent_filter)

    historiques = []
    for agent in agents:
        measurements = Measurement.objects.filter(user=agent)
        retours = RetourEffet.objects.filter(agent=agent)
        if date_debut:
            measurements = measurements.filter(created_at__date__gte=date_debut)
            retours = retours.filter(created_at__date__gte=date_debut)
        if date_fin:
            measurements = measurements.filter(created_at__date__lte=date_fin)
            retours = retours.filter(created_at__date__lte=date_fin)
        historiques.append({
            'agent': agent,
            'measurements': measurements,
            'retours': retours,
        })

    return render(request, 'admin_panel/historique.html', {
        'historiques': historiques,
        'agents': User.objects.filter(role='agent').order_by('nom'),
        'agent_filter': agent_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
    })


# ─── EXPORT EXCEL ─────────────────────────────────────────
@role_required(['admin'])
def export_historique_excel(request):
    from accounts.models import User
    from datetime import datetime
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Historique par agent"

    # ── Colors ──
    navy_fill = PatternFill(start_color="1A3A6B", end_color="1A3A6B", fill_type="solid")
    navy_dark_fill = PatternFill(start_color="0F2444", end_color="0F2444", fill_type="solid")
    gold_fill = PatternFill(start_color="C8A84B", end_color="C8A84B", fill_type="solid")
    light_gray_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    header_demande_fill = PatternFill(start_color="1A3A6B", end_color="1A3A6B", fill_type="solid")
    header_retour_fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
    white_font = Font(bold=True, color="FFFFFF", size=9)
    white_font_lg = Font(bold=True, color="FFFFFF", size=14)
    white_font_sm = Font(bold=False, color="B0C4DE", size=8)
    title_font = Font(bold=True, color="1A3A6B", size=12)
    subtitle_font = Font(bold=False, color="64748B", size=8)
    agent_font = Font(bold=True, color="1A3A6B", size=9)
    data_font = Font(size=8.5)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1'),
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(vertical="center")

    # ── Header block (rows 1-3) ──
    # Row 1: colored background bar
    for col in range(1, 12):
        cell = ws.cell(row=1, column=col)
        cell.fill = navy_fill
        cell.border = thin_border
    ws.merge_cells('A1:K1')
    title_cell = ws.cell(row=1, column=1)
    title_cell.value = "ADII — Administration des Douanes et Impôts Indirects"
    title_cell.font = white_font_lg
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    # Gold accent bar
    ws.row_dimensions[1].height = 32

    # Row 2: subtitle
    for col in range(1, 12):
        cell = ws.cell(row=2, column=col)
        cell.fill = navy_fill
        cell.border = thin_border
    ws.merge_cells('A2:K2')
    sub_cell = ws.cell(row=2, column=1)
    sub_cell.value = "GESTION D'HABILLEMENT — Rapport historique par agent"
    sub_cell.font = white_font_sm
    sub_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 18

    # Row 3: gold separator
    for col in range(1, 12):
        cell = ws.cell(row=3, column=col)
        cell.fill = gold_fill
        cell.border = thin_border
    ws.row_dimensions[3].height = 4

    # Row 4: report info
    ws.merge_cells('A4:K4')
    info_cell = ws.cell(row=4, column=1)
    now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    agent_filter_str = request.GET.get('agent', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    filter_text = "Tous les agents"
    if agent_filter_str:
        filter_agent = User.objects.filter(pk=agent_filter_str).first()
        if filter_agent:
            filter_text = filter_agent.get_full_name()
    info_cell.value = f"Généré le {now_str} — Filtre : {filter_text}"
    if date_debut or date_fin:
        info_cell.value += f" — Période : {date_debut or '...'} au {date_fin or '...'}"
    info_cell.font = subtitle_font
    info_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[4].height = 22

    # Row 5: empty spacer
    ws.row_dimensions[5].height = 6

    # ── Data header row (row 6) ──
    data_start_row = 6
    demande_headers = ["Agent", "Matricule", "Service",
                       "Date demande", "Type équipement", "Statut"]
    retour_headers = ["Date retour", "Type équipement", "Quantité", "Motif retour", "Notes"]

    # Demande headers (blue)
    for col, h in enumerate(demande_headers, 1):
        cell = ws.cell(row=data_start_row, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF", size=8)
        cell.fill = header_demande_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Retour headers (red)
    for col, h in enumerate(retour_headers, 7):
        cell = ws.cell(row=data_start_row, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF", size=8)
        cell.fill = header_retour_fill
        cell.alignment = center_align
        cell.border = thin_border

    ws.row_dimensions[data_start_row].height = 22

    # ── Data rows ──
    row = data_start_row + 1
    agent_filter_val = request.GET.get('agent', '')
    date_debut_val = request.GET.get('date_debut', '')
    date_fin_val = request.GET.get('date_fin', '')

    agents_qs = User.objects.filter(role='agent').order_by('nom')
    if agent_filter_val:
        agents_qs = agents_qs.filter(pk=agent_filter_val)

    for agent in agents_qs:
        measurements = Measurement.objects.filter(user=agent)
        retours = RetourEffet.objects.filter(agent=agent)
        if date_debut_val:
            measurements = measurements.filter(created_at__date__gte=date_debut_val)
            retours = retours.filter(created_at__date__gte=date_debut_val)
        if date_fin_val:
            measurements = measurements.filter(created_at__date__lte=date_fin_val)
            retours = retours.filter(created_at__date__lte=date_fin_val)

        measurements = list(measurements)
        retours = list(retours)
        max_rows = max(len(measurements), len(retours), 1)

        for i in range(max_rows):
            m = measurements[i] if i < len(measurements) else None
            r = retours[i] if i < len(retours) else None
            is_even = (row % 2 == 0)

            # Agent info (cols 1-3)
            if i == 0:
                ws.cell(row=row, column=1, value=agent.get_full_name()).font = agent_font
                ws.cell(row=row, column=2, value=agent.matricule or '').font = data_font
                ws.cell(row=row, column=3, value=agent.service or '').font = data_font
            else:
                ws.cell(row=row, column=1, value='').font = data_font
                ws.cell(row=row, column=2, value='').font = data_font
                ws.cell(row=row, column=3, value='').font = data_font

            # Demande data (cols 4-6)
            if m:
                ws.cell(row=row, column=4, value=m.created_at.strftime('%d/%m/%Y')).font = data_font
                ws.cell(row=row, column=5, value=m.get_type_equipement_display()).font = data_font
                ws.cell(row=row, column=6, value=m.get_status_display()).font = Font(size=8.5, bold=True,
                    color='065F46' if m.status == 'livre' else
                          '065F46' if m.status == 'pret' else
                          '5B21B6' if m.status == 'en_production' else
                          '1E40AF' if m.status == 'valide' else
                          '991B1B' if m.status == 'refuse' else '92400E')
            else:
                for c in [4, 5, 6]:
                    ws.cell(row=row, column=c, value='').font = data_font

            # Retour data (cols 7-11)
            if r:
                ws.cell(row=row, column=7, value=r.created_at.strftime('%d/%m/%Y')).font = data_font
                ws.cell(row=row, column=8, value=r.get_type_equipement_display()).font = data_font
                ws.cell(row=row, column=9, value=r.quantite).font = Font(size=8.5, bold=True)
                ws.cell(row=row, column=10, value=r.get_motif_display()).font = Font(size=8.5,
                    color='991B1B' if r.motif == 'destruction' else
                          '92400E' if r.motif == 'perte' else
                          '3730A3' if r.motif == 'usure' else '475569')
                ws.cell(row=row, column=11, value=r.notes or '—').font = data_font
            else:
                for c in [7, 8, 9, 10, 11]:
                    ws.cell(row=row, column=c, value='').font = data_font

            # Borders and row shading
            bg = light_gray_fill if is_even else PatternFill(fill_type=None)
            for col in range(1, 12):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.alignment = left_align
                if not (col == 6 and m):
                    cell.fill = bg

            ws.row_dimensions[row].height = 18
            row += 1

    # ── Column widths ──
    col_widths = [22, 12, 14, 14, 18, 14, 14, 18, 10, 14, 20]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── Freeze panes ──
    ws.freeze_panes = f'A{data_start_row + 1}'

    # ── Print setup ──
    ws.sheet_properties.pageSetUpPr = openpyxl.worksheet.properties.PageSetupProperties(fitToPage=True)
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    # ── Response ──
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = "historique_agents.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ─── EXPORT PDF ───────────────────────────────────────────
def _draw_header(canvas, doc):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4, landscape
    w, h = landscape(A4)
    canvas.saveState()
    # Header background
    canvas.setFillColor(colors.HexColor('#1A3A6B'))
    canvas.roundRect(0.8*cm, h - 1.6*cm, w - 1.6*cm, 1.1*cm, 4, fill=1, stroke=0)
    # Logo shield
    canvas.setFillColor(colors.HexColor('#C8A84B'))
    cx, cy = 1.5*cm, h - 1.05*cm
    canvas.setStrokeColor(colors.HexColor('#A8882B'))
    canvas.setLineWidth(1.2)
    p = canvas.beginPath()
    p.moveTo(cx-12, cy-10)
    p.lineTo(cx, cy-18)
    p.lineTo(cx+12, cy-10)
    p.lineTo(cx+12, cy+8)
    p.lineTo(cx, cy+18)
    p.lineTo(cx-12, cy+8)
    p.close()
    canvas.drawPath(p, fill=1, stroke=1)
    canvas.setFillColor(colors.HexColor('#1A3A6B'))
    canvas.setFont('Times-Bold', 9)
    canvas.drawCentredString(cx, cy-5, 'ADII')
    # Title
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawString(2.5*cm, h - 1.35*cm, 'ADII — Gestion d\'habillement')
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#B0C4DE'))
    canvas.drawString(2.5*cm, h - 1.55*cm, 'Administration des Douanes et Impôts Indirects')
    # Divider
    canvas.setStrokeColor(colors.HexColor('#B0C4DE'))
    canvas.setLineWidth(0.5)
    canvas.line(10.5*cm, h - 1.05*cm, 10.5*cm, h - 1.55*cm)
    # Right side
    canvas.setFillColor(colors.HexColor('#B0C4DE'))
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawRightString(w - 1.5*cm, h - 1.2*cm, 'RAPPORT')
    canvas.setStrokeColor(colors.HexColor('#C8A84B'))
    canvas.setLineWidth(2)
    canvas.line(w - 3.5*cm, h - 1.28*cm, w - 1.5*cm, h - 1.28*cm)
    canvas.setFillColor(colors.HexColor('#90A4C4'))
    canvas.setFont('Helvetica', 6.5)
    canvas.drawRightString(w - 1.5*cm, h - 1.45*cm, 'Historique par agent')
    # Footer
    canvas.setFillColor(colors.HexColor('#94A3B8'))
    canvas.setFont('Helvetica', 6.5)
    canvas.drawCentredString(w/2, 0.5*cm,
        f'ADII — Administration des Douanes et Impôts Indirects — Page {doc.page} / {{TBD}}')
    canvas.restoreState()


def _render_pdf_reportlab(historiques, agents, agent_filter, date_debut, date_fin):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, PageBreak)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        title="Historique par agent",
        topMargin=2.2*cm, bottomMargin=1.2*cm,
        leftMargin=1.2*cm, rightMargin=1.2*cm,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=13, textColor=colors.HexColor('#1A3A6B'),
        spaceAfter=2, spaceBefore=2,
    )
    subtitle_style = ParagraphStyle(
        'ReportSub', parent=styles['Normal'],
        fontSize=7.5, textColor=colors.HexColor('#64748B'),
        spaceAfter=14,
    )
    agent_heading = ParagraphStyle(
        'AgentHead', parent=styles['Heading2'],
        fontSize=10, textColor=colors.HexColor('#1A3A6B'),
        spaceBefore=4, spaceAfter=2,
    )
    section_label = ParagraphStyle(
        'SectionLbl', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#334155'),
        spaceBefore=6, spaceAfter=2,
    )

    elements = []

    # Report info line
    from datetime import datetime
    elements.append(Paragraph("Historique par agent", title_style))
    filter_parts = [f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}"]
    filter_parts.append('Agent spécifique' if agent_filter else 'Tous les agents')
    if date_debut or date_fin:
        filter_parts.append(f"Du {date_debut or '...'} au {date_fin or '...'}")
    elements.append(Paragraph(' · '.join(filter_parts), subtitle_style))
    # Separator
    sep_data = [['', '']]
    sep_table = Table(sep_data, colWidths=[landscape(A4)[0] - 2.4*cm, 0])
    sep_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(sep_table)
    elements.append(Spacer(1, 3))

    for h in historiques:
        agent = h['agent']
        measurements = list(h['measurements'])
        retours = list(h['retours'])
        if not measurements and not retours:
            continue

        agent_info = f"{agent.get_full_name()} — {agent.matricule or 'N/A'} — {agent.service or 'N/A'}"
        badge_text = f"  [{len(measurements)} demande(s) | {len(retours)} retour(s)]"
        elements.append(Paragraph(agent_info + badge_text, agent_heading))

        if measurements:
            elements.append(Paragraph("<b>📋 Demandes d'équipement</b>", section_label))
            data = [["Date", "Type d'équipement", "Statut", "Rempli par"]]
            for m in measurements:
                rempli = m.rempli_par.get_full_name() or m.rempli_par.username if m.rempli_par else '—'
                data.append([
                    m.created_at.strftime('%d/%m/%Y'),
                    m.get_type_equipement_display(),
                    m.get_status_display(),
                    rempli,
                ])
            table = Table(data, colWidths=[70, 130, 90, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A3A6B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 4))

        if retours:
            elements.append(Paragraph("<b>🔄 Retours d'effets</b>", section_label))
            data = [["Date", "Type d'équipement", "Qté", "Motif", "Notes"]]
            for r in retours:
                data.append([
                    r.created_at.strftime('%d/%m/%Y'),
                    r.get_type_equipement_display(),
                    str(r.quantite),
                    r.get_motif_display(),
                    r.notes or '—',
                ])
            table = Table(data, colWidths=[70, 130, 40, 70, 90])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFF5F5'), colors.HexColor('#FFF0F0')]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 6))

    doc.build(elements, onFirstPage=_draw_header, onLaterPages=_draw_header)
    buffer.seek(0)
    return buffer


@role_required(['admin'])
def export_historique_pdf(request):
    from accounts.models import User
    agent_filter = request.GET.get('agent', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    agents_qs = User.objects.filter(role='agent').order_by('nom')
    if agent_filter:
        agents_qs = agents_qs.filter(pk=agent_filter)

    historiques = []
    for agent in agents_qs:
        measurements = Measurement.objects.filter(user=agent)
        retours = RetourEffet.objects.filter(agent=agent)
        if date_debut:
            measurements = measurements.filter(created_at__date__gte=date_debut)
            retours = retours.filter(created_at__date__gte=date_debut)
        if date_fin:
            measurements = measurements.filter(created_at__date__lte=date_fin)
            retours = retours.filter(created_at__date__lte=date_fin)
        historiques.append({
            'agent': agent,
            'measurements': measurements,
            'retours': retours,
        })

    try:
        import weasyprint
        html = render_to_string('admin_panel/historique_pdf.html', {
            'historiques': historiques,
            'agent_filter': agent_filter,
            'date_debut': date_debut,
            'date_fin': date_fin,
        })
        from pathlib import Path
        pdf = weasyprint.HTML(string=html, base_url=Path(__file__).resolve().parent.parent).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="historique_agents.pdf"'
        return response
    except (ImportError, OSError):
        buffer = _render_pdf_reportlab(historiques, agents_qs, agent_filter, date_debut, date_fin)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="historique_agents.pdf"'
        return response


@login_required
def measurement_detail(request, pk):
    m = get_object_or_404(Measurement, pk=pk)
    if request.user.role == 'agent' and m.user != request.user:
        return redirect('home')
    return render(request, 'measurement_detail.html', {'m': m})