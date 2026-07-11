from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from measurements.models import Measurement, RetourEffet
from stock.models import StockItem, StockMovement
from notifications.models import Notification
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Populate the database with demo users and sample data'

    def handle(self, *args, **options):
        self._create_users()
        self._create_stock_items()
        self._create_measurements()
        self._create_retours()
        self._create_notifications()
        self.stdout.write(self.style.SUCCESS('Database populated successfully'))

    def _create_users(self):
        users_data = [
            {'username': 'admin@adii.ma', 'password': 'Admin2026!', 'role': 'admin', 'nom': 'Admin', 'prenom': 'Super', 'matricule': 'ADM001', 'service': 'Administration'},
            {'username': 'agent@adii.ma', 'password': 'Agent2026!', 'role': 'agent', 'nom': 'Alaoui', 'prenom': 'Ahmed', 'matricule': 'AGT001', 'service': 'Production'},
            {'username': 'agent2@adii.ma', 'password': 'Agent2026!', 'role': 'agent', 'nom': 'Benani', 'prenom': 'Sara', 'matricule': 'AGT002', 'service': 'Production'},
            {'username': 'tech@adii.ma', 'password': 'Tech2026!', 'role': 'technicien', 'nom': 'Idrissi', 'prenom': 'Karim', 'matricule': 'TEC001', 'service': 'Technique'},
            {'username': 'secretaire@adii.ma', 'password': 'Secretaire2026!', 'role': 'secretaire', 'nom': 'El Amrani', 'prenom': 'Fatima', 'matricule': 'SEC001', 'service': 'Secrétariat'},
        ]
        for data in users_data:
            User.objects.update_or_create(
                username=data['username'],
                defaults={
                    'email': data['username'],
                    'role': data['role'],
                    'nom': data['nom'],
                    'prenom': data['prenom'],
                    'matricule': data['matricule'],
                    'service': data['service'],
                }
            )
        for data in users_data:
            u = User.objects.get(username=data['username'])
            u.set_password(data['password'])
            u.save()
        self.stdout.write(f'  Created {len(users_data)} users')

    def _create_stock_items(self):
        items = [
            {'name': 'Veste été', 'category': 'veste', 'size': 'M', 'quantity': 15, 'min_threshold': 5},
            {'name': 'Veste été', 'category': 'veste', 'size': 'L', 'quantity': 20, 'min_threshold': 5},
            {'name': 'Pantalon été', 'category': 'pantalon', 'size': 'M', 'quantity': 3, 'min_threshold': 10},
            {'name': 'Pantalon été', 'category': 'pantalon', 'size': 'L', 'quantity': 25, 'min_threshold': 10},
            {'name': 'Chemise manches longues', 'category': 'chemise', 'size': 'S', 'quantity': 8, 'min_threshold': 5},
            {'name': 'Chemise manches longues', 'category': 'chemise', 'size': 'M', 'quantity': 0, 'min_threshold': 5},
            {'name': 'Chemise manches longues', 'category': 'chemise', 'size': 'L', 'quantity': 12, 'min_threshold': 5},
            {'name': 'Uniforme été complet', 'category': 'uniforme_ete', 'size': 'M', 'quantity': 10, 'min_threshold': 5},
            {'name': 'Uniforme été complet', 'category': 'uniforme_ete', 'size': 'L', 'quantity': 7, 'min_threshold': 5},
            {'name': 'Uniforme hiver complet', 'category': 'uniforme_hiver', 'size': 'XL', 'quantity': 4, 'min_threshold': 5},
        ]
        for item in items:
            StockItem.objects.update_or_create(
                name=item['name'], category=item['category'], size=item['size'],
                defaults={'quantity': item['quantity'], 'min_threshold': item['min_threshold']}
            )
        self.stdout.write(f'  Created {len(items)} stock items')

    def _create_measurements(self):
        admin = User.objects.get(username='admin@adii.ma')
        agent = User.objects.get(username='agent@adii.ma')
        agent2 = User.objects.get(username='agent2@adii.ma')

        measurements_data = [
            {'user': agent, 'rempli_par': admin, 'type_equipement': 'uniforme_ete', 'tour_poitrine': 96, 'tour_taille': 82, 'tour_hanches': 98, 'epaules': 44, 'manche': 62, 'entrejambe': 78, 'status': 'valide', 'notes_admin': 'OK'},
            {'user': agent, 'rempli_par': admin, 'type_equipement': 'veste', 'tour_poitrine': 96, 'tour_taille': 82, 'tour_hanches': 98, 'epaules': 44, 'manche': 62, 'entrejambe': 78, 'status': 'en_production', 'notes_admin': ''},
            {'user': agent2, 'rempli_par': admin, 'type_equipement': 'pantalon', 'tour_poitrine': 88, 'tour_taille': 74, 'tour_hanches': 92, 'epaules': 40, 'manche': 58, 'entrejambe': 80, 'status': 'en_attente', 'notes_admin': ''},
            {'user': agent2, 'rempli_par': None, 'type_equipement': 'chemise', 'tour_poitrine': 88, 'tour_taille': 74, 'tour_hanches': 92, 'epaules': 40, 'manche': 58, 'entrejambe': 80, 'status': 'en_attente', 'notes_admin': ''},
        ]
        for data in measurements_data:
            Measurement.objects.create(**data)
        self.stdout.write(f'  Created {len(measurements_data)} measurements')

    def _create_retours(self):
        admin = User.objects.get(username='admin@adii.ma')
        agent = User.objects.get(username='agent@adii.ma')
        agent2 = User.objects.get(username='agent2@adii.ma')
        retours_data = [
            {'agent': agent, 'type_equipement': 'veste', 'quantite': 2, 'motif': 'usure', 'notes': 'Vestes usagées retournées', 'created_by': agent},
            {'agent': agent, 'type_equipement': 'pantalon', 'quantite': 1, 'motif': 'destruction', 'notes': 'Pantalon déchiré', 'created_by': agent},
            {'agent': agent2, 'type_equipement': 'chemise', 'quantite': 3, 'motif': 'usure', 'notes': 'Chemises hors d\'usage', 'created_by': agent2},
        ]
        for data in retours_data:
            RetourEffet.objects.create(**data)
        self.stdout.write(f'  Created {len(retours_data)} returns')

    def _create_notifications(self):
        users = User.objects.all()
        notifications_data = [
            {'user': random.choice(users), 'title': 'Nouvelle fiche de mesure', 'message': 'Une nouvelle fiche de mesure a été soumise.', 'category': 'measurement'},
            {'user': random.choice(users), 'title': 'Stock bas', 'message': 'Le stock de Chemise manches longues (M) est épuisé.', 'category': 'stock'},
            {'user': random.choice(users), 'title': 'Fiche validée', 'message': 'La fiche de mesure de Ahmed Alaoui a été validée.', 'category': 'measurement'},
        ]
        for data in notifications_data:
            Notification.objects.create(**data)
        self.stdout.write(f'  Created {len(notifications_data)} notifications')
