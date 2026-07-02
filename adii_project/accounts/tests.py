from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import User
from .views import get_redirect

UserModel = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', email='agent@test.com',
            password='pass1234', role='agent',
            nom='Dupont', prenom='Jean', matricule='A001', service='Bureau'
        )
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', email='admin@test.com',
            password='pass1234', role='admin',
            nom='Martin', prenom='Marie'
        )
        self.tech = UserModel.objects.create_user(
            username='tech@test.com', email='tech@test.com',
            password='pass1234', role='technicien'
        )
        self.sec = UserModel.objects.create_user(
            username='sec@test.com', email='sec@test.com',
            password='pass1234', role='secretaire'
        )

    def test_role_helpers(self):
        self.assertTrue(self.agent.is_agent())
        self.assertFalse(self.agent.is_admin())
        self.assertFalse(self.agent.is_technicien())
        self.assertFalse(self.agent.is_secretaire())
        self.assertTrue(self.admin.is_admin())
        self.assertTrue(self.tech.is_technicien())
        self.assertTrue(self.sec.is_secretaire())

    def test_get_full_name_with_prenom_nom(self):
        self.assertEqual(self.agent.get_full_name(), 'Jean Dupont')

    def test_get_full_name_fallback_to_username(self):
        self.assertEqual(self.tech.get_full_name(), 'tech@test.com')

    def test_default_role_is_agent(self):
        user = UserModel.objects.create_user(username='new@test.com', password='pass')
        self.assertEqual(user.role, 'agent')

    def test_str(self):
        self.assertEqual(str(self.agent), 'agent@test.com')


class GetRedirectTest(TestCase):
    def test_get_redirect_admin(self):
        user = User(role='admin')
        self.assertEqual(get_redirect(user), '/admin-dashboard/')

    def test_get_redirect_technicien(self):
        user = User(role='technicien')
        self.assertEqual(get_redirect(user), '/technicien/')

    def test_get_redirect_secretaire(self):
        user = User(role='secretaire')
        self.assertEqual(get_redirect(user), '/secretaire/')

    def test_get_redirect_agent(self):
        user = User(role='agent')
        self.assertEqual(get_redirect(user), '/agent/')


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', email='agent@test.com',
            password='pass1234', role='agent'
        )
        self.admin_user = UserModel.objects.create_user(
            username='admin@test.com', email='admin@test.com',
            password='pass1234', role='admin'
        )
        self.tech = UserModel.objects.create_user(
            username='tech@test.com', email='tech@test.com',
            password='pass1234', role='technicien'
        )

    def test_login_page_get(self):
        response = self.client.get(reverse('auth'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth.html')

    def test_login_success_agent(self):
        response = self.client.post(reverse('auth'), {
            'action': 'login', 'username': 'agent@test.com', 'password': 'pass1234'
        })
        self.assertRedirects(response, '/agent/')

    def test_login_success_admin(self):
        response = self.client.post(reverse('auth') + '?mode=admin', {
            'action': 'login', 'username': 'admin@test.com', 'password': 'pass1234'
        })
        self.assertRedirects(response, '/admin-dashboard/')

    def test_login_wrong_password(self):
        response = self.client.post(reverse('auth'), {
            'action': 'login', 'username': 'agent@test.com', 'password': 'wrong'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email ou mot de passe incorrect')

    def test_login_admin_mode_rejects_agent(self):
        response = self.client.post(reverse('auth') + '?mode=admin', {
            'action': 'login', 'username': 'agent@test.com', 'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Accès refusé')

    def test_login_technicien_mode_rejects_agent(self):
        response = self.client.post(reverse('auth') + '?mode=technicien', {
            'action': 'login', 'username': 'agent@test.com', 'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Accès refusé')

    def test_register_creates_agent(self):
        response = self.client.post(reverse('auth'), {
            'action': 'register',
            'email': 'new@test.com',
            'nom': 'Test', 'prenom': 'User',
            'matricule': 'M001', 'service': 'IT',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertRedirects(response, reverse('agent_dashboard'))
        user = UserModel.objects.get(email='new@test.com')
        self.assertEqual(user.role, 'agent')
        self.assertEqual(user.username, 'new@test.com')

    def test_logout(self):
        self.client.login(username='agent@test.com', password='pass1234')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))

    def test_profile_get(self):
        self.client.login(username='agent@test.com', password='pass1234')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_profile_post(self):
        self.client.login(username='agent@test.com', password='pass1234')
        response = self.client.post(reverse('profile'), {
            'nom': 'Updated', 'prenom': 'Name',
            'matricule': 'A999', 'service': 'New',
            'email': 'agent@test.com'
        })
        self.assertRedirects(response, reverse('profile'))
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.nom, 'Updated')

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f'/auth/login/?next={reverse("profile")}')

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
