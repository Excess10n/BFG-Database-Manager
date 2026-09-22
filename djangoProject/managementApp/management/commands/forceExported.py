from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import Record
import datetime


class Command(BaseCommand):
    help = 'Force all records to be tagged as exported'

    def handle(self, *args, **options):
        for rec in Record.objects.all():
            if not rec.exported:
                rec.exported = True
                rec.dateExported = datetime.datetime.today()
                rec.save()
