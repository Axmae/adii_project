from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Notification
from .utils import create_notification
from .context_processors import unread_notifications

UserModel = get_user_model()


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent'
        )
        self.notif = Notification.objects.create(
            user=self.user, title='Test Title',
            message='Test message', category='measurement'
        )

    def test_creation(self):
        self.assertEqual(str(self.notif), 'agent@test.com — Test Title')
        self.assertFalse(self.notif.read)
        self.assertIsNotNone(self.notif.created_at)

    def test_default_category(self):
        n = Notification.objects.create(
            user=self.user, title='System', message='Test'
        )
        self.assertEqual(n.category, 'system')

    def test_ordering(self):
        n2 = Notification.objects.create(
            user=self.user, title='Second', message='Test'
        )
        notifs = Notification.objects.all()
        self.assertEqual(notifs.first(), n2)


class CreateNotificationUtilTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent'
        )

    def test_create_notification_default_category(self):
        create_notification(self.user, 'Title', 'Message')
        notif = Notification.objects.first()
        self.assertEqual(notif.title, 'Title')
        self.assertEqual(notif.message, 'Message')
        self.assertEqual(notif.category, 'system')
        self.assertFalse(notif.read)

    def test_create_notification_with_category(self):
        create_notification(self.user, 'Stock Alert', 'Low!', category='stock')
        notif = Notification.objects.first()
        self.assertEqual(notif.category, 'stock')


class NotificationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserModel.objects.create_user(
            username='user@test.com', password='pass', role='agent'
        )
        self.other = UserModel.objects.create_user(
            username='other@test.com', password='pass', role='agent'
        )
        self.notif = Notification.objects.create(
            user=self.user, title='My Notif', message='Read me'
        )
        Notification.objects.create(
            user=self.other, title='Other Notif', message='Not mine'
        )
        self.client.login(username='user@test.com', password='pass')

    def test_notifications_list(self):
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Notif')
        self.assertNotContains(response, 'Other Notif')

    def test_notifications_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('notifications'))
        self.assertRedirects(
            response, f'/auth/login/?next={reverse("notifications")}'
        )

    def test_mark_read(self):
        response = self.client.get(
            reverse('mark_read', args=[self.notif.pk]),
            HTTP_REFERER=reverse('notifications')
        )
        self.assertRedirects(response, reverse('notifications'))
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.read)

    def test_mark_read_other_users_notification(self):
        other_notif = Notification.objects.filter(user=self.other).first()
        response = self.client.get(
            reverse('mark_read', args=[other_notif.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read(self):
        Notification.objects.create(
            user=self.user, title='Unread 2', message='Test'
        )
        response = self.client.get(
            reverse('mark_all_read'),
            HTTP_REFERER=reverse('notifications')
        )
        self.assertRedirects(response, reverse('notifications'))
        unread = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread, 0)


class ContextProcessorTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            username='user@test.com', password='pass', role='agent'
        )

    def test_unread_count_authenticated(self):
        Notification.objects.create(user=self.user, title='N1', message='M1')
        Notification.objects.create(user=self.user, title='N2', message='M2')
        Notification.objects.create(
            user=self.user, title='N3', message='M3', read=True
        )
        class MockRequest:
            user = self.user
        result = unread_notifications(MockRequest())
        self.assertEqual(result['unread_count'], 2)

    def test_unauthenticated_returns_empty(self):
        from django.contrib.auth.models import AnonymousUser
        class MockRequest:
            user = AnonymousUser()
        result = unread_notifications(MockRequest())
        self.assertEqual(result['unread_count'], 0)
        self.assertEqual(result['unread_notifications'], [])
