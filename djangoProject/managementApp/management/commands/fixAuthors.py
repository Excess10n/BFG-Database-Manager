from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import Fungi
import json
import os
ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        with open(ROOT_DIR + '/failedAuthors.json') as json_file:
            authors = json.load(json_file)
        
        for fun in Fungi.objects.filter(author__icontains="ï¿½", currentName=None):
            try:
                fun.author = authors[fun.author]
                fun.save()
                #print(fun.author)
            except:
                print(f"{fun.author} failed")
                pass
            
