from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Measurement, RetourEffet
from .views import role_required
from stock.models import StockItem, StockMovement
from notifications.models import Notification

UserModel = get_user_model()


class MeasurementModelTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.m = Measurement.objects.create(
            user=self.user, rempli_par=self.user,
            type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )

    def test_creation_defaults(self):
        self.assertEqual(self.m.status, 'en_attente')
        self.assertIsNotNone(self.m.created_at)
        self.assertIsNotNone(self.m.updated_at)

    def test_str(self):
        expected = f"Jean Dupont — Uniforme été (En attente)"
        self.assertEqual(str(self.m), expected)

    def test_status_color(self):
        self.assertEqual(self.m.status_color(), 'amber')
        self.m.status = 'valide'
        self.assertEqual(self.m.status_color(), 'blue')
        self.m.status = 'en_production'
        self.assertEqual(self.m.status_color(), 'purple')
        self.m.status = 'pret'
        self.assertEqual(self.m.status_color(), 'teal')
        self.m.status = 'livre'
        self.assertEqual(self.m.status_color(), 'green')
        self.m.status = 'refuse'
        self.assertEqual(self.m.status_color(), 'red')

    def test_can_edit_when_en_attente(self):
        self.assertTrue(self.m.can_edit())

    def test_cannot_edit_when_not_en_attente(self):
        for s in ['valide', 'en_production', 'pret', 'livre', 'refuse']:
            self.m.status = s
            self.assertFalse(self.m.can_edit())

    def test_default_ordering(self):
        m2 = Measurement.objects.create(
            user=self.user, rempli_par=self.user,
            type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        qs = Measurement.objects.all()
        self.assertEqual(qs.first(), m2)


class RoleRequiredDecoratorTest(TestCase):
    def setUp(self):
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent'
        )
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin'
        )

    def test_role_required_allows_correct_role(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_role_required_redirects_wrong_role(self):
        self.client.login(username='agent@test.com', password='pass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(response, reverse('home'))

    def test_role_required_redirects_unauthenticated(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(response, reverse('auth'))


class AgentFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin'
        )
        self.client.login(username='agent@test.com', password='pass')

    def test_agent_dashboard_shows_own_measurements(self):
        m1 = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        other = UserModel.objects.create_user(
            username='other@test.com', password='pass', role='agent'
        )
        Measurement.objects.create(
            user=other, rempli_par=other, type_equipement='chemise',
            tour_poitrine=90, tour_taille=70, tour_hanches=80,
            epaules=40, manche=55, entrejambe=70,
        )
        response = self.client.get(reverse('agent_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Veste')
        self.assertNotContains(response, 'Chemise')

    def test_create_measurement(self):
        response = self.client.post(reverse('create_measurement'), {
            'type_equipement': 'uniforme_ete',
            'tour_poitrine': 100, 'tour_taille': 80, 'tour_hanches': 90,
            'epaules': 45, 'manche': 60, 'entrejambe': 75,
        })
        self.assertRedirects(response, reverse('agent_dashboard'))
        self.assertEqual(Measurement.objects.count(), 1)
        m = Measurement.objects.first()
        self.assertEqual(m.user, self.agent)
        self.assertEqual(m.rempli_par, self.agent)

    def test_create_measurement_notifies_admins(self):
        self.client.post(reverse('create_measurement'), {
            'type_equipement': 'uniforme_ete',
            'tour_poitrine': 100, 'tour_taille': 80, 'tour_hanches': 90,
            'epaules': 45, 'manche': 60, 'entrejambe': 75,
        })
        notif = Notification.objects.filter(user=self.admin).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.category, 'measurement')
        self.assertIn('Jean Dupont', notif.message)

    def test_create_duplicate_blocked(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.post(reverse('create_measurement'), {
            'type_equipement': 'uniforme_ete',
            'tour_poitrine': 100, 'tour_taille': 80, 'tour_hanches': 90,
            'epaules': 45, 'manche': 60, 'entrejambe': 75,
        }, follow=True)
        self.assertContains(response, 'déjà une fiche en cours')

    def test_create_allows_when_previous_is_livre(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='livre'
        )
        response = self.client.post(reverse('create_measurement'), {
            'type_equipement': 'uniforme_ete',
            'tour_poitrine': 100, 'tour_taille': 80, 'tour_hanches': 90,
            'epaules': 45, 'manche': 60, 'entrejambe': 75,
        })
        self.assertRedirects(response, reverse('agent_dashboard'))
        self.assertEqual(Measurement.objects.count(), 2)

    def test_edit_measurement(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.post(
            reverse('edit_measurement', args=[m.pk]),
            {'type_equipement': 'chemise', 'tour_poitrine': 95,
             'tour_taille': 75, 'tour_hanches': 85,
             'epaules': 42, 'manche': 58, 'entrejambe': 72}
        )
        self.assertRedirects(response, reverse('agent_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.type_equipement, 'chemise')

    def test_edit_blocked_when_not_en_attente(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        response = self.client.get(
            reverse('edit_measurement', args=[m.pk])
        )
        self.assertRedirects(response, reverse('agent_dashboard'))

    def test_agent_cannot_view_other_measurement_detail(self):
        other = UserModel.objects.create_user(
            username='other@test.com', password='pass', role='agent'
        )
        m = Measurement.objects.create(
            user=other, rempli_par=other, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.get(reverse('measurement_detail', args=[m.pk]))
        self.assertRedirects(response, reverse('home'))


class SecretaireFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.secretaire = UserModel.objects.create_user(
            username='sec@test.com', password='pass', role='secretaire',
            nom='Secret', prenom='Anna'
        )
        self.client.login(username='sec@test.com', password='pass')

    def test_secretaire_dashboard(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.get(reverse('secretaire_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Veste')

    def test_secretaire_create_for_agent(self):
        response = self.client.post(reverse('secretaire_create'), {
            'agent_id': self.agent.pk,
            'type_equipement': 'uniforme_hiver',
            'tour_poitrine': 100, 'tour_taille': 80, 'tour_hanches': 90,
            'epaules': 45, 'manche': 60, 'entrejambe': 75,
        })
        self.assertRedirects(response, reverse('secretaire_dashboard'))
        m = Measurement.objects.first()
        self.assertEqual(m.user, self.agent)
        self.assertEqual(m.rempli_par, self.secretaire)

    def test_secretaire_create_blocked_if_agent_has_active(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.post(reverse('secretaire_create'), {
            'agent_id': self.agent.pk,
            'type_equipement': 'uniforme_hiver',
            'tour_poitrine': 100, 'tour_taille': 80, 'tour_hanches': 90,
            'epaules': 45, 'manche': 60, 'entrejambe': 75,
        })
        self.assertRedirects(response, reverse('secretaire_dashboard'))
        self.assertEqual(Measurement.objects.count(), 1)


class AdminFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin',
            nom='Admin', prenom='Boss'
        )
        self.tech = UserModel.objects.create_user(
            username='tech@test.com', password='pass', role='technicien'
        )
        self.client.login(username='admin@test.com', password='pass')

    def test_admin_dashboard(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Veste')

    def test_admin_dashboard_shows_stats(self):
        for i in range(3):
            Measurement.objects.create(
                user=self.agent, rempli_par=self.agent, type_equipement='veste',
                tour_poitrine=100, tour_taille=80, tour_hanches=90,
                epaules=45, manche=60, entrejambe=75,
                status='en_attente'
            )
        response = self.client.get(reverse('admin_dashboard'))
        self.assertContains(response, '3')

    def test_validate_measurement(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.post(
            reverse('validate_measurement', args=[m.pk]),
            {'action': 'valide'}
        )
        self.assertRedirects(response, reverse('admin_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'valide')

    def test_validate_notifies_tech_and_agent(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        self.client.post(
            reverse('validate_measurement', args=[m.pk]),
            {'action': 'valide'}
        )
        self.assertTrue(
            Notification.objects.filter(user=self.tech, category='measurement').exists()
        )
        self.assertTrue(
            Notification.objects.filter(user=self.agent, category='measurement').exists()
        )

    def test_refuse_measurement(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        response = self.client.post(
            reverse('validate_measurement', args=[m.pk]),
            {'action': 'refuse', 'notes_admin': 'Mesures incorrectes'}
        )
        self.assertRedirects(response, reverse('admin_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'refuse')
        self.assertEqual(m.notes_admin, 'Mesures incorrectes')

    def test_manage_users(self):
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jean Dupont')

    def test_change_role(self):
        response = self.client.post(
            reverse('change_role', args=[self.agent.pk]),
            {'role': 'technicien'}
        )
        self.assertRedirects(response, reverse('manage_users'))
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.role, 'technicien')

    def test_change_role_invalid_ignored(self):
        response = self.client.post(
            reverse('change_role', args=[self.agent.pk]),
            {'role': 'invalid'}
        )
        self.assertRedirects(response, reverse('manage_users'))
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.role, 'agent')

    def test_livraison_groupee(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='pret'
        )
        response = self.client.get(reverse('livraison_groupee'))
        self.assertEqual(response.status_code, 200)

    def test_confirmer_livraison_groupee(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='pret'
        )
        response = self.client.post(
            reverse('confirmer_livraison_groupee'),
            {'fiche_ids': [str(m.pk)]}
        )
        self.assertRedirects(response, reverse('livraison_groupee'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'livre')

    def test_confirmer_livraison_groupee_no_selection(self):
        response = self.client.post(
            reverse('confirmer_livraison_groupee'), {}
        )
        self.assertRedirects(response, reverse('livraison_groupee'))

    def test_avancement_groupe(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='chemise',
            tour_poitrine=90, tour_taille=70, tour_hanches=80,
            epaules=40, manche=55, entrejambe=70,
        )
        response = self.client.get(reverse('avancement_groupe'))
        self.assertEqual(response.status_code, 200)

    def test_avancement_groupe_with_filters(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='chemise',
            tour_poitrine=90, tour_taille=70, tour_hanches=80,
            epaules=40, manche=55, entrejambe=70,
        )
        response = self.client.get(
            reverse('avancement_groupe'),
            {'agent': self.agent.pk, 'status': 'en_attente'}
        )
        self.assertEqual(response.status_code, 200)


class TechFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.tech = UserModel.objects.create_user(
            username='tech@test.com', password='pass', role='technicien',
            nom='Tech', prenom='Bob'
        )
        self.admin_user = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin'
        )
        self.client.login(username='tech@test.com', password='pass')

    def test_tech_dashboard(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        response = self.client.get(reverse('tech_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Veste')

    def test_tech_dashboard_excludes_en_attente(self):
        Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='en_attente'
        )
        response = self.client.get(reverse('tech_dashboard'))
        self.assertNotContains(response, 'Veste')

    def test_update_status_valide_to_en_production(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        response = self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'en_production'}
        )
        self.assertRedirects(response, reverse('tech_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'en_production')

    def test_update_status_en_production_to_pret(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='en_production'
        )
        response = self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'pret'}
        )
        self.assertRedirects(response, reverse('tech_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'pret')

    def test_update_status_pret_to_livre(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='pret'
        )
        response = self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'livre'}
        )
        self.assertRedirects(response, reverse('tech_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'livre')

    def test_update_status_invalid_transition(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='en_attente'
        )
        response = self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'en_production'}
        )
        self.assertRedirects(response, reverse('tech_dashboard'))
        m.refresh_from_db()
        self.assertEqual(m.status, 'en_attente')

    def test_update_status_to_en_production_decrements_stock(self):
        StockItem.objects.create(
            name='T-shirt été', category='uniforme_ete', size='M',
            quantity=10, min_threshold=5
        )
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'en_production'}
        )
        item = StockItem.objects.first()
        self.assertEqual(item.quantity, 9)
        movement = StockMovement.objects.first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.type, 'sortie')
        self.assertEqual(movement.reason, 'production')
        self.assertEqual(movement.quantity, 1)
        self.assertEqual(movement.quantity_before, 10)
        self.assertEqual(movement.quantity_after, 9)

    def test_update_status_to_en_production_triggers_low_stock_notification(self):
        StockItem.objects.create(
            name='T-shirt été', category='uniforme_ete', size='M',
            quantity=1, min_threshold=5
        )
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'en_production'}
        )
        notif = Notification.objects.filter(
            user=self.admin_user, category='stock'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('Stock bas', notif.title)

    def test_update_status_notifies_agent(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        self.client.post(
            reverse('update_status', args=[m.pk]),
            {'status': 'en_production'}
        )
        notif = Notification.objects.filter(
            user=self.agent, category='measurement'
        ).first()
        self.assertIsNotNone(notif)

    def test_measurement_detail_agent_can_view_own(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        self.client.login(username='agent@test.com', password='pass')
        response = self.client.get(reverse('measurement_detail', args=[m.pk]))
        self.assertEqual(response.status_code, 200)

    def test_measurement_detail_admin_can_view_any(self):
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('measurement_detail', args=[m.pk]))
        self.assertEqual(response.status_code, 200)

    def test_confirmer_avancement_groupe_decrements_stock(self):
        StockItem.objects.create(
            name='T-shirt été', category='uniforme_ete', size='M',
            quantity=10, min_threshold=5
        )
        m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='uniforme_ete',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75, status='valide'
        )
        self.client.login(username='admin@test.com', password='pass')
        self.client.post(reverse('confirmer_avancement_groupe'), {
            'fiche_ids': [str(m.pk)],
            'new_status': 'en_production'
        })
        item = StockItem.objects.first()
        self.assertEqual(item.quantity, 9)


class PermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent'
        )
        self.tech = UserModel.objects.create_user(
            username='tech@test.com', password='pass', role='technicien'
        )

    def test_agent_cannot_access_tech_dashboard(self):
        self.client.login(username='agent@test.com', password='pass')
        response = self.client.get(reverse('tech_dashboard'))
        self.assertRedirects(response, reverse('home'))

    def test_tech_cannot_access_admin_dashboard(self):
        self.client.login(username='tech@test.com', password='pass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(response, reverse('home'))


# ─── RETOUR EFFET ────────────────────────────────────────

class RetourEffetModelTest(TestCase):
    def setUp(self):
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.retour = RetourEffet.objects.create(
            agent=self.agent, type_equipement='veste',
            quantite=2, motif='destruction',
            notes='Usagé', created_by=self.agent
        )

    def test_creation(self):
        self.assertEqual(self.retour.quantite, 2)
        self.assertEqual(self.retour.motif, 'destruction')
        self.assertIsNotNone(self.retour.created_at)

    def test_str(self):
        expected = "Jean Dupont — Veste x2 (Destruction)"
        self.assertEqual(str(self.retour), expected)

    def test_default_ordering(self):
        r2 = RetourEffet.objects.create(
            agent=self.agent, type_equipement='chemise',
            quantite=1, motif='usure'
        )
        qs = RetourEffet.objects.all()
        self.assertEqual(qs.first(), r2)


class RetourEffetFormAgentFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean'
        )
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin',
            nom='Admin', prenom='Boss'
        )
        self.client.login(username='agent@test.com', password='pass')

    def test_retour_page_get(self):
        response = self.client.get(reverse('enregistrer_retour'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'agent/retour.html')

    def test_retour_submit(self):
        response = self.client.post(reverse('enregistrer_retour'), {
            'type_equipement': 'veste',
            'quantite': 3,
            'motif': 'destruction',
            'notes': 'Anciennes vestes',
        })
        self.assertRedirects(response, reverse('agent_dashboard'))
        self.assertEqual(RetourEffet.objects.count(), 1)
        r = RetourEffet.objects.first()
        self.assertEqual(r.agent, self.agent)
        self.assertEqual(r.quantite, 3)
        self.assertEqual(r.motif, 'destruction')
        self.assertEqual(r.created_by, self.agent)

    def test_retour_notifies_admin(self):
        self.client.post(reverse('enregistrer_retour'), {
            'type_equipement': 'pantalon',
            'quantite': 1,
            'motif': 'usure',
        })
        notif = Notification.objects.filter(
            user=self.admin, category='stock'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('retourné', notif.message)

    def test_retour_agent_only(self):
        self.client.logout()
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('enregistrer_retour'))
        self.assertRedirects(response, reverse('home'))


# ─── HISTORIQUE AGENTS (Admin) ───────────────────────────

class HistoriqueAgentsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin',
            nom='Admin', prenom='Boss'
        )
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent',
            nom='Dupont', prenom='Jean', matricule='A001', service='Prod'
        )
        self.m = Measurement.objects.create(
            user=self.agent, rempli_par=self.agent, type_equipement='veste',
            tour_poitrine=100, tour_taille=80, tour_hanches=90,
            epaules=45, manche=60, entrejambe=75,
        )
        self.r = RetourEffet.objects.create(
            agent=self.agent, type_equipement='chemise',
            quantite=2, motif='destruction', created_by=self.agent
        )
        self.client.login(username='admin@test.com', password='pass')

    def test_historique_page_get(self):
        response = self.client.get(reverse('historique_agents'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/historique.html')

    def test_historique_shows_agent_data(self):
        response = self.client.get(reverse('historique_agents'))
        self.assertContains(response, 'Jean Dupont')
        self.assertContains(response, 'Veste')
        self.assertContains(response, 'Chemise')

    def test_historique_requires_admin(self):
        self.client.logout()
        self.client.login(username='agent@test.com', password='pass')
        response = self.client.get(reverse('historique_agents'))
        self.assertRedirects(response, reverse('home'))

    def test_historique_filter_by_agent(self):
        response = self.client.get(
            reverse('historique_agents'),
            {'agent': self.agent.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jean Dupont')

    def test_historique_excel_export(self):
        response = self.client.get(reverse('export_historique_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])

    def test_historique_pdf_export(self):
        response = self.client.get(reverse('export_historique_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
