from .models import Notification

def create_notification(user, title, message, category='system'):
    Notification.objects.create(user=user, title=title, message=message, category=category)
