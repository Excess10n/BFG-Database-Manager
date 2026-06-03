from django.core.management.base import BaseCommand
from ...models import Member, Manager, Fungi, FungiArchive, Group, Genus, Site, Association, Substrate, Record, RecordArchive
from django.contrib.auth.models import User
import os

ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = 'yay'
    def handle(self, *args, **options):
        Record.objects.all().delete()
        RecordArchive.objects.all().delete()
        Fungi.objects.all().delete()
        FungiArchive.objects.all().delete()
        Group.objects.all().delete()
        Genus.objects.all().delete()
        Site.objects.all().delete()
        Association.objects.all().delete()
        Substrate.objects.all().delete()
        Member.objects.all().delete()
        Manager.objects.all().delete()

        User.objects.all().delete()