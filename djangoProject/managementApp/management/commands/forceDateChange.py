from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import Record
import datetime
import json
import os

ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = 'Force all records to be tagged as exported'

    def handle(self, *args, **options):
        print("forcing date change...")
        
        with open(ROOT_DIR + '/newDates.json') as json_file:
            newDates = json.load(json_file)

        count = 0
        for rec in Record.objects.all():
            for newDate in newDates:
                if rec.uniqueCode == newDate["uniqueCode"]:
                    rec.dateFound = datetime.datetime.strptime(newDate["dateFound"], "%d/%m/%Y %H:%M").date()
                    rec.dateEntered = datetime.datetime.strptime(newDate["dateEntered"], "%d/%m/%Y %H:%M").date()
                    rec.dateUpdated = datetime.datetime.today()
                    rec.save()
                    count += 1

        print(f"completed force date change with {count} records")
