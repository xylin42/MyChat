from django.core.management import BaseCommand
from django.urls import resolve


class Command(BaseCommand):
   def handle(self, *args, **options):
      res = resolve('users/1/events')
