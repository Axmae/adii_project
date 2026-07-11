from unittest.mock import patch, ANY

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from .models import Notification
from .utils import create_notification
from .context_processors import unread_notifications
from .email_utils import send_welcome_email, send_status_email
from measurements.models import Measurement

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


class EmailUtilsTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            username='jean@test.com', email='jean@test.com',
            password='pass', role='agent',
            nom='Dupont', prenom='Jean', matricule='A001', service='Prod'
        )

    @patch('notifications.email_utils._send_async')
    def test_send_welcome_email(self, mock_send):
        send_welcome_email(self.user)
        msg = mock_send.call_args[0][0]
        self.assertEqual(msg.to, ['jean@test.com'])
        self.assertIn('Bienvenue', msg.subject)
        self.assertIn('Jean', msg.alternatives[0][0])
        self.assertEqual(msg.alternatives[0][1], 'text/html')

    @patch('notifications.email_utils._send_async')
    def test_send_status_email(self, mock_send):
        m = Measurement.objects.create(
            user=self.user, rempli_par=self.user,
            type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        send_status_email(m)
        msg = mock_send.call_args[0][0]
        self.assertEqual(msg.to, ['jean@test.com'])
        self.assertIn('Mise à jour', msg.subject)
        self.assertIn('En attente', msg.alternatives[0][0])
        self.assertIn('Uniforme été', msg.alternatives[0][0])

    @patch('notifications.email_utils._send_async')
    def test_send_status_email_with_admin_note(self, mock_send):
        m = Measurement.objects.create(
            user=self.user, rempli_par=self.user,
            type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
            status='refuse', notes_admin='Mesures invalides'
        )
        send_status_email(m)
        msg = mock_send.call_args[0][0]
        content = msg.alternatives[0][0]
        self.assertIn('Mesures invalides', content)
        self.assertIn('Refusé', content)

    @patch('notifications.email_utils._send_async')
    def test_send_email_constructs_message(self, mock_send):
        from notifications.email_utils import _send_email
        _send_email(
            'jean@test.com',
            'Sujet test',
            'emails/welcome.html',
            {'user': self.user},
        )
        msg = mock_send.call_args[0][0]
        self.assertEqual(msg.to, ['jean@test.com'])
        self.assertEqual(msg.subject, 'Sujet test')
        self.assertEqual(msg.from_email, 'ADII <noreply@adii.ma>')
        html = msg.alternatives[0][0]
        self.assertIn('Jean', html)
        self.assertEqual(msg.alternatives[0][1], 'text/html')

    def test_welcome_email_template_renders(self):
        from django.template.loader import render_to_string
        html = render_to_string('emails/welcome.html', {'user': self.user, 'login_url': '/'})
        self.assertIn('Jean Dupont', html)
        self.assertIn('Bienvenue', html)
        self.assertIn('A001', html)
        self.assertIn('Prod', html)

    def test_status_email_template_renders(self):
        m = Measurement.objects.create(
            user=self.user, rempli_par=self.user,
            type_equipement='uniforme_hiver',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
            status='valide',
        )
        from django.template.loader import render_to_string
        html = render_to_string('emails/status_update.html', {'m': m, 'status': m.get_status_display()})
        self.assertIn('Uniforme hiver', html)
        self.assertIn('Validé', html)

    def test_password_reset_email_template_renders(self):
        from django.template.loader import render_to_string
        html = render_to_string('emails/password_reset.html', {
            'protocol': 'http',
            'domain': 'example.com',
            'uid': 'MQ',
            'token': 'abc123',
            'timeout_days': 3,
        })
        self.assertIn('http://example.com', html)
        self.assertIn('MQ', html)
        self.assertIn('abc123', html)


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
