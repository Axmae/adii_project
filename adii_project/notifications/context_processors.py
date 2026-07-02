from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        notifs = Notification.objects.filter(user=request.user, read=False)[:10]
        return {'unread_notifications': notifs, 'unread_count': notifs.count()}
    return {'unread_notifications': [], 'unread_count': 0}
