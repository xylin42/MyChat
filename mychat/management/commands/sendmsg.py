from datetime import datetime

from django.core.management import BaseCommand

from mychat.models import User, Conversation
from mychat.services.conversation import send_message


class Command(BaseCommand):
   def handle(self, *args, **options):
      conv = Conversation.objects.get(user1_id=1, user2_id=2)
      body = datetime.now().strftime('%H:%M:%S')
      send_message(conv.id, 2, 1, body)
