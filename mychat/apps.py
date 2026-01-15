from django.apps import AppConfig
from django.conf import settings


class MyChatConfig(AppConfig):
   name = 'mychat'

   def ready(self):
      pass