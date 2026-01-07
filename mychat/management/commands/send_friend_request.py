from django.core.management import BaseCommand

from mychat.models import FriendRequest
from mychat.services.friendship import send_friend_request


class Command(BaseCommand):
   def handle(self, *args, **options):
      try:
         FriendRequest.objects.filter(user1_id=1, user2_id=5).delete()
         print('删除已存在的请求')
      except:
         pass
      print('发送新的朋友请求')
      send_friend_request(5, 1)
