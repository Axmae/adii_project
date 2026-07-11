from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import StockItem, StockMovement
from notifications.models import Notification

UserModel = get_user_model()


class StockItemModelTest(TestCase):
    def setUp(self):
        self.item = StockItem.objects.create(
            name='T-shirt été', category='uniforme_ete', size='M',
            quantity=10, min_threshold=5
        )

    def test_creation(self):
        self.assertEqual(str(self.item), 'T-shirt été — M (10)')

    def test_is_low_below_threshold(self):
        self.item.quantity = 3
        self.assertTrue(self.item.is_low())

    def test_is_low_at_threshold(self):
        self.item.quantity = 5
        self.assertFalse(self.item.is_low())

    def test_is_low_above_threshold(self):
        self.item.quantity = 10
        self.assertFalse(self.item.is_low())

    def test_status_label_epuise(self):
        self.item.quantity = 0
        label, color = self.item.status_label()
        self.assertEqual(label, 'Épuisé')
        self.assertEqual(color, 'red')

    def test_status_label_stock_bas(self):
        self.item.quantity = 3
        label, color = self.item.status_label()
        self.assertEqual(label, 'Stock bas')
        self.assertEqual(color, 'amber')

    def test_status_label_disponible(self):
        self.item.quantity = 10
        label, color = self.item.status_label()
        self.assertEqual(label, 'Disponible')
        self.assertEqual(color, 'green')

    def test_default_ordering(self):
        StockItem.objects.create(
            name='Veste hiver', category='uniforme_hiver', size='L',
            quantity=5, min_threshold=3
        )
        items = StockItem.objects.all()
        self.assertEqual(items[0].category, 'uniforme_ete')
        self.assertEqual(items[1].category, 'uniforme_hiver')

    def test_default_min_threshold(self):
        item = StockItem.objects.create(
            name='Chemise', category='chemise', size='M', quantity=10
        )
        self.assertEqual(item.min_threshold, 5)


class StockMovementModelTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            username='tech@test.com', password='pass', role='technicien'
        )
        self.item = StockItem.objects.create(
            name='Test', category='veste', size='M',
            quantity=10, min_threshold=3
        )
        self.movement = StockMovement.objects.create(
            stock_item=self.item, type='sortie', reason='production',
            quantity=2, quantity_before=10, quantity_after=8,
            note='Test', created_by=self.user
        )

    def test_creation(self):
        self.assertEqual(str(self.movement), 'Sortie — Test (2)')

    def test_ordering(self):
        m2 = StockMovement.objects.create(
            stock_item=self.item, type='entree', reason='livraison_fournisseur',
            quantity=5, quantity_before=8, quantity_after=13,
            created_by=self.user
        )
        movements = StockMovement.objects.all()
        self.assertEqual(movements.first(), m2)


class StockViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = UserModel.objects.create_user(
            username='admin@test.com', password='pass', role='admin',
            nom='Admin', prenom='Boss'
        )
        self.tech = UserModel.objects.create_user(
            username='tech@test.com', password='pass', role='technicien',
            nom='Tech', prenom='Bob'
        )
        self.agent = UserModel.objects.create_user(
            username='agent@test.com', password='pass', role='agent'
        )
        self.item = StockItem.objects.create(
            name='T-shirt été', category='uniforme_ete', size='M',
            quantity=10, min_threshold=5
        )

    def test_stock_list_as_tech(self):
        self.client.login(username='tech@test.com', password='pass')
        response = self.client.get(reverse('stock_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'T-shirt été')

    def test_stock_list_as_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('stock_list'))
        self.assertEqual(response.status_code, 200)

    def test_stock_list_denies_agent(self):
        self.client.login(username='agent@test.com', password='pass')
        response = self.client.get(reverse('stock_list'))
        self.assertRedirects(response, reverse('home'))

    def test_stock_list_denies_unauthenticated(self):
        response = self.client.get(reverse('stock_list'))
        self.assertRedirects(response, reverse('home'))

    def test_stock_add(self):
        self.client.login(username='tech@test.com', password='pass')
        response = self.client.post(reverse('stock_add'), {
            'name': 'Veste hiver', 'category': 'uniforme_hiver',
            'size': 'L', 'quantity': 20, 'min_threshold': 5
        })
        self.assertRedirects(response, reverse('stock_list'))
        self.assertEqual(StockItem.objects.count(), 2)

    def test_stock_edit(self):
        self.client.login(username='tech@test.com', password='pass')
        response = self.client.post(
            reverse('stock_edit', args=[self.item.pk]),
            {'name': 'T-shirt été V2', 'category': 'uniforme_ete',
             'size': 'M', 'quantity': 15, 'min_threshold': 5}
        )
        self.assertRedirects(response, reverse('stock_list'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'T-shirt été V2')
        self.assertEqual(self.item.quantity, 15)

    def test_stock_movement_entry(self):
        self.client.login(username='tech@test.com', password='pass')
        response = self.client.post(
            reverse('stock_movement', args=[self.item.pk]),
            {'type': 'entree', 'reason': 'livraison_fournisseur',
             'quantity': 5, 'note': 'New delivery'}
        )
        self.assertRedirects(response, reverse('stock_list'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 15)
        movement = StockMovement.objects.first()
        self.assertEqual(movement.type, 'entree')
        self.assertEqual(movement.quantity_before, 10)
        self.assertEqual(movement.quantity_after, 15)

    def test_stock_movement_exit(self):
        self.client.login(username='tech@test.com', password='pass')
        response = self.client.post(
            reverse('stock_movement', args=[self.item.pk]),
            {'type': 'sortie', 'reason': 'production',
             'quantity': 3, 'note': 'Used in production'}
        )
        self.assertRedirects(response, reverse('stock_list'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 7)

    def test_stock_movement_insufficient_stock(self):
        self.client.login(username='tech@test.com', password='pass')
        self.item.quantity = 2
        self.item.save()
        response = self.client.post(
            reverse('stock_movement', args=[self.item.pk]),
            {'type': 'sortie', 'reason': 'production',
             'quantity': 5, 'note': ''}
        )
        self.assertRedirects(response, reverse('stock_movement', args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)

    def test_stock_movement_low_stock_notification(self):
        self.client.login(username='tech@test.com', password='pass')
        self.item.quantity = 3
        self.item.min_threshold = 5
        self.item.save()
        self.client.post(
            reverse('stock_movement', args=[self.item.pk]),
            {'type': 'sortie', 'reason': 'perte',
             'quantity': 1, 'note': ''}
        )
        notif = Notification.objects.filter(
            user=self.admin, category='stock'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('Stock bas', notif.title)

    def test_stock_movements_all(self):
        self.client.login(username='tech@test.com', password='pass')
        StockMovement.objects.create(
            stock_item=self.item, type='entree', reason='livraison_fournisseur',
            quantity=5, quantity_before=10, quantity_after=15,
            created_by=self.tech
        )
        response = self.client.get(reverse('stock_movements_all'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entrée')

    def test_stock_movements_all_filter_by_type(self):
        self.client.login(username='tech@test.com', password='pass')
        StockMovement.objects.create(
            stock_item=self.item, type='entree', reason='livraison_fournisseur',
            quantity=5, quantity_before=10, quantity_after=15,
            created_by=self.tech
        )
        response = self.client.get(
            reverse('stock_movements_all'), {'type': 'entree'}
        )
        self.assertEqual(response.status_code, 200)

    def test_stock_movements_all_filter_by_search(self):
        self.client.login(username='tech@test.com', password='pass')
        StockMovement.objects.create(
            stock_item=self.item, type='entree', reason='livraison_fournisseur',
            quantity=5, quantity_before=10, quantity_after=15,
            note='Urgent restock', created_by=self.tech
        )
        response = self.client.get(
            reverse('stock_movements_all'), {'search': 'Urgent'}
        )
        self.assertEqual(response.status_code, 200)
