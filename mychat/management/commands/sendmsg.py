from datetime import datetime

from django.core.management import BaseCommand
from django.utils import timezone

from mychat.models import Conversation, user_pair
from mychat.services.conversation import send_message


class Command(BaseCommand):
   def handle(self, *args, **options):
      conv = user_pair.get_model_instance(Conversation, 1, 2)
      localdate = timezone.datetime.now().strftime('%H:%M:%S')
      body = "现在是: " + localdate
      send_message(conv.id, 2, 1, body)
