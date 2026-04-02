from django.core.management.base import BaseCommand
from ...models import Member, Manager, Fungi, FungiArchive, Group, Genus, Site, Association, Substrate, Record, RecordArchive
import os

ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = 'yay'
    def handle(self, *args, **options):
        print(Fungi.objects.get(fullName="Russula gilva ").fullName)