from django.core.management.base import BaseCommand
from ...models import Member, Manager, Fungi, FungiArchive, Group, Genus, Site, Association, Substrate, Record, RecordArchive
from django.contrib.auth.models import User
import os

ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = 'yay'
    def handle(self, *args, **options):
        from django.core.management.utils import get_random_secret_key

        print(get_random_secret_key())