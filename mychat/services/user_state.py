from django.db.models import F

from mychat.models import User


def incr_unread_friend_requests(userid):
   User.objects.filter(id=userid).update(
      unread_friend_requests = F('unread_friend_requests')
   )
