from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a default superuser if one does not already exist'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'AdminUser'
        password = 'ChangeThisPassword'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, None, password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser already exists: {username}'))
