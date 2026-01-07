from django.core.cache import cache

from mychat.models import User

def inc_total_unread(user_id, count=1):
   1

def get_total_unread(user_id):
   key = f'mychat:total_unread:{user_id}'

   def load_from_db():
      return User.objects.get(id=user_id).total_unread

   return cache.get_or_set(key, load_from_db, timeout=30)
