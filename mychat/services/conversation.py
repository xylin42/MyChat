import functools
import struct

from django.db import transaction
from django.db.models import F
from django.forms import model_to_dict
from django.utils import timezone

from mychat.events import user_event
from mychat.models import Conversation, Friendship, UserConvState, user_pair, Message
from mychat.utils.redis_client import RedisHash, redis_write_pipeline
from mychat.utils.redis_client import RedisMixin, \
   redis_read_pipeline


def create_conversation_state_with_friend(conv_id, user_id, peer_id):
   friend_id = Friendship.objects.filter(user_id=user_id, friend_user_id=peer_id).values_list(flat=True).first()

   if not friend_id:
      raise ValueError('不是朋友')

   return UserConvState.objects.create(conv_id=conv_id, user_id=user_id, peer_id=peer_id, friend_id=friend_id)


def create_unique_conversation(user1, user2):
   conv = user_pair.create_model_instance(Conversation, user1, user2)

   create_conversation_state_with_friend(conv.id, user1, user2)
   create_conversation_state_with_friend(conv.id, user2, user1)

   return conv


class UserConvStateCache(RedisHash):
   encode_field_mappings = {
      'last_read_seq': 'l',
   }

   @classmethod
   def get_instance_key(self, state):
      return f'ucs:{state.user_id}:{state.conv_id}'


class ConversationCache(RedisHash):
   encode_field_mappings = {
      'last_seq': 'l',
      'last_msg_preview_encoded': 'p',
   }

   @staticmethod
   def encode_message_preview(conv):
      created_at = struct.pack('f', conv.last_msg_date.timestamp())
      return bytes(conv.last_msg_preview, 'utf-8') + b'\x00' + created_at

   @staticmethod
   def decode_message_preview(bs):
      msg, ts = bs.split(b'\x00')
      msg = msg.decode('utf-8')
      ts = struct.unpack('f', ts)
      date = timezone.localtime(
         timezone.datetime.fromtimestamp(ts, tz=timezone.utc)
      )
      return msg, date

   def set(self, conv):
      encoded = self.encode_message_preview(conv)
      return super().set(last_msg_preview_encoded=encoded, last_seq=conv.last_seq)

   def decode(self):
      preview, created_at = self.decode_message_preview(self.last_msg_preview_encoded)
      self.last_msg_preview = preview
      self.last_msg_date = created_at
      return self.__dict__

   def __init__(self, conv_id):
      self.key = f'convs:{conv_id}'

def render_user_conv_state_to_client(state):
   pass

class UserConvListCache(RedisMixin):
   def __init__(self, user_id):
      self.user_id = user_id
      self.key = f'convs:u:{user_id}'

   def lock(self):
      return self.wclient.lock(f'lock:{self.key}')

   def get_since(self, since):
      pass

   def reload_all(self):
      states_qs = UserConvState.objects.filter(user_id=self.user_id) \
         .select_related('friend__friend_user', "conv").order_by('-conv__last_msg_date')
      states = []
      friends = []
      with self.lock():
         with redis_write_pipeline() as pipe:
            for state in states_qs:
               self.add(state, need_lock=False)

               states.append(state.render_to_client())
               friends.append(state.friend.render_to_client())

            pipe.client.zrevrange(self.key, 0, 1, withscores=True)
      latest_date = pipe.result[-1][0][1]
      return states, friends, latest_date

   def add(self, state, need_lock=True):
      def do_add():
         state_key = f'ucs:{state.user_id}:{state.conv_id}'
         flat = [x for kv in UserConvStateCache.get_encoded_mapping(state).items() for x in kv]
         return self.wclient.eval("""
         if redis.call("zadd", KEYS[1], "GT", "CH", ARGV[1], ARGV[2]) then
            redis.call("hset", KEYS[2], unpack(ARGV, 3))
            return true
         else
            return false
         end
         """, 2, self.key, state_key, state.conv.id, state.conv.last_msg_date.timestamp(), *flat)

      if need_lock:
         with self.lock():
            updated = do_add()
            if updated:
               user_event.publish_new_message(state.user_id, state.render_to_client())
      else:
         do_add()

@transaction.atomic
def send_message(conv_id, sender_id, recipient_id, body):
   Conversation.objects.filter(pk=conv_id).update(last_seq=F('last_seq') + 1)

   last_seq = Conversation.objects.values_list('last_seq', flat=True).get(pk=conv_id)
   msg = Message.objects.create(body=body, conv_id=conv_id, seq=last_seq, sender_id=sender_id)

   last_msg_date = msg.created_at
   last_msg_date_local = timezone.localtime(last_msg_date)

   Conversation.objects.filter(pk=conv_id).update(last_msg_preview=body, last_msg_date=msg.created_at)

   UserConvState.objects.filter(user_id=sender_id, conv_id=conv_id).update(last_read_seq=last_seq)

   def on_commit():
      conv = Conversation(id=conv_id, last_seq=last_seq, last_msg_preview=body, last_msg_date=msg.created_at)
      recipient_state = UserConvState(user_id=recipient_id, conv=conv)
      sender_state = UserConvState(user_id=sender_id, last_read_seq=last_seq, conv=conv)

      UserConvListCache(recipient_id).add(recipient_state)
      UserConvListCache(sender_id).add(sender_state)


   transaction.on_commit(on_commit)

   return None
