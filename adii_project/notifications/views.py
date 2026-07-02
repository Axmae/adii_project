from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.read = True
    n.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def notifications_list(request):
    from django.shortcuts import render
    notifs = Notification.objects.filter(user=request.user)
    return render(request, 'notifications.html', {'notifications': notifs})
