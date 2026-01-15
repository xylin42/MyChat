import json

from django.core.cache import cache
from django.db.models import F

from mychat.models import User




class UserStateCache:
   def __init__(self, userid):
      self.redis = cache._cache.get_client(write=True)
      self.userid=userid
      self.key = f'user-state:{userid}'

   def decode(self, data):
      return {k.decode('utf-8'): v.decode('utf-8') for k,v in data.items()}

   def ensure_exists(self):
      return self.get(check_exists_only=True)

   def json(self):
      data = self.get()
      return json.dumps(data)

   def get(self, check_exists_only=False):
      redis = self.redis
      key = self.key

      if data := redis.hgetall(key):
         if check_exists_only:
            return
         return self.decode(data)

      redis = cache._cache.get_client(write=True)
      lock = f'lock:{key}'

      with redis.lock(lock):
         if data := redis.hgetall(key):
            if check_exists_only:
               return
            return self.decode(data)

         state = User.objects.values('unread_friend_requests').get(id=self.userid)
         redis.hset(key, mapping=state)
         return state

   def incr_field(self, field):
      self.ensure_exists()
      return self.redis.hincrby(self.key, field, 1)


def incr_user_state_field(userid, field):
   redis = cache._cahce.get_client(write=True)
   ensure_user_state_exists(userid)
   redis.hincrby(f"user-state:{userid}", field, 1)

def ensure_user_state_exists(userid):
   key = f"user-state:{userid}"
   if state := cache.get(key):
      return state
   redis = cache._cache.get_client(write=True)
   lock = f'lock:{key}'
   with redis.lock(lock):
      if state := cache.get(key):
         return state
      state = User.objects.values('unread_friend_requests', flat=True).get(id=userid)
      redis.set(key, state)
      return state

def incr_unread_friend_requests(userid):
   User.objects.filter(id=userid).update(
      unread_friend_requests = F('unread_friend_requests')
   )
   return UserStateCache(userid).incr_field('unread_friend_requests')