from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...viewFunctions import getAllSimilarFungi
from ...models import Record
import datetime
import json
import os

ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        print("resetting recent firsts...")
        
        for inst in Record.objects.filter(dateUpdated__gt=datetime.date(2026, 9, 1)):
            inst.firstRecord = 'N'
            similars = getAllSimilarFungi(inst.fungusFK)
            site_history = list(
                Record.objects.filter(fungusFK__in=similars, dateFound__lt=inst.dateFound)
                .values_list("siteFK_id", "siteFK__VC")
            )
            if not site_history:
                inst.firstRecord = 'D'
            elif not any(vic == 24 for _, vic in site_history) and inst.siteFK.VC == 24:
                inst.firstRecord = 'B'
            elif not any(site_id == inst.siteFK_id for site_id, _ in site_history):
                inst.firstRecord = 'S'
            inst.save()

        print(f"completed first reset")
