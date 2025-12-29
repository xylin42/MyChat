import os

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
   def handle(self, *args, **options):
      try:
         os.remove(settings.DATABASES['contrib']['NAME'])
      except FileNotFoundError:
         pass
      call_command('migrate', '--database=contrib')
