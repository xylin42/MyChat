from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django_redis import get_redis_connection

from mychat.events import user_event
from mychat.models import FriendRequest, Friendship, User
from mychat.services import user_state

incr_if_exists = """
if redis.call("exists", KEYS[1]) == 1 then
   return redis.call("incr", KEYS[1])
else
   return nil
end
"""

def django_redis_eval(script):
   client = cache._cache.get_client(write=True)
   client.eval(script)

def raw_redis_client():
   return cache._cache.get_client()

def redis_locked_incr(key, loader):
   redis = cache._cache.get_client(write=True)

   if v := redis.eval(incr_if_exists) is not None:
      return int(v)

   if not v:
      locked_key = f'lock:{key}'
      with redis.lock(locked_key):
         v = redis.eval(incr_if_exists)
         if not v:
            v = loader()
            v += 1
            redis.set(key, v)

   return v

@transaction.atomic
def establish_friendship(user, friend, remark=None):
   Friendship.objects.create(user_id=user, friend_id=friend, remark=remark or "")

def incr_unread_friend_requests(recipient):
   User.objects.filter(id=recipient).update(unread_friend_requests=F('unread_friend_requests')+1)
   key = f'unread_friend_requests:user:{recipient}'

   def load_from_db():
      return User.objects.get(id=recipient).unread_friend_requests

   return redis_locked_incr(key, load_from_db)

@transaction.atomic
def send_friend_request(requester, recipient):
   user1, user2 = sorted((requester, recipient))
   req = FriendRequest.objects.create(user1_id=user1, user2_id=user2, requester_id=requester)

   unread = user_state.incr_unread_friend_requests(recipient)

   transaction.on_commit(user_event.get_publish_func(recipient, "friend-request-received", {
      'unread': unread
   }))

   return req