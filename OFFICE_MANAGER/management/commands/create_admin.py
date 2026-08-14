from django.core.management.base import BaseCommand
from OFFICE_MANAGER.models import User


class Command(BaseCommand):
    help = 'Creates the initial Admin user for OFFICE_MANAGER (Developer Setup)'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Admin username')
        parser.add_argument('--email', type=str, default='admin@example.com', help='Admin email')
        parser.add_argument('--password', type=str, default='admin123', help='Admin password')
        parser.add_argument('--phone', type=str, default='', help='Admin phone number')
        parser.add_argument('--address', type=str, default='', help='Admin address')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        phone = options['phone']
        address = options['address']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User with username '{username}' already exists."))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User with email '{email}' already exists."))
            return

        admin_user = User.objects.create(
            username=username,
            email=email,
            password=password,  # Plain text password per project requirement
            role=User.ROLE_ADMIN,
            phone=phone,
            address=address
        )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created initial Admin account!\n"
            f"ID: {admin_user.id}\n"
            f"Username: {admin_user.username}\n"
            f"Email: {admin_user.email}\n"
            f"Role: {admin_user.role}"
        ))
