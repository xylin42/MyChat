from django.db import transaction
from django.db.models import F

from mychat.events import user_event
from mychat.models import Conversation, User, Friendship, ConversationState


def create_conversation_state_with_friend(conv_id, user_id, peer_id):
   friend_id = Friendship.objects.filter(user_id=user_id, friend_id=peer_id).values_list(flat=True).first()
   if not friend_id:
      raise ValueError('不是朋友')
   return ConversationState.objects.create(conv_id=conv_id, user_id=user_id, peer_id=peer_id, friend_id=friend_id)


def get_unique_conversation(user1, user2):
   user1, user2 = sorted((user1, user2))
   conv, created = Conversation.objects.get_or_create(user1_id=user1, user2_id=user2)

   if created:
      create_conversation_state_with_friend(conv.id, user1, user2)
      create_conversation_state_with_friend(conv.id, user2, user1)

   return conv, created

@transaction.atomic
def send_message(conv_id, sender_id, recipient_id, body):
   if conv_id is None:
      conv, created = get_unique_conversation(sender_id, recipient_id)
   else:
      conv = Conversation.objects.select_for_update().get(id=conv_id)
   conv.last_seq += 1

   msg = conv.messages.create(body=body, conv_id=conv.id, seq=conv.last_seq, sender_id=sender_id)
   conv.last_msg = msg
   conv.save(update_fields=['last_seq', 'last_msg'])
   User.objects.filter(id=recipient_id).update(
      total_unread=F('total_unread') + 1,
   )

   data = dict(
      seq=msg.seq, body=body, sender_id=msg.sender.id,
   )

   transaction.on_commit(user_event.get_publish_func(recipient_id, 'message-arrived'))
   return data
