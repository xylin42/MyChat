import hashlib
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string

from mychat.models import Conversation, User, UserConvState

@transaction.atomic
def start_conversation(initiator, peer):
   conv = Conversation.objects.create(member1=initiator, member2=peer)
   id = '{0}-{1}'.format(*sorted((initiator.id, peer.id)))
   hashed_id = hashlib.blake2b(id.encode('utf-8'), digest_size=8).hexdigest()
   UserConvState.objects.bulk_create([
      UserConvState(user=initiator, peer=peer, conv=conv),
      UserConvState(user=peer, peer=initiator, conv=conv),
   ])
   return conv

@transaction.atomic
def send_message(conv_id, sender_id, recipient_id, body):
   if conv_id is None:
      conv, created = Conversation.objects.get_or_create_by_id_pair((sender_id, recipient_id))
   else:
      conv = Conversation.objects.select_for_update().get(id=conv_id)
   conv.last_seq += 1

   msg = conv.messages.create(body=body, conv_id=conv.id, seq=conv.last_seq, sender_id=sender_id)
   conv.last_msg = msg
   conv.save(update_fields=['last_seq', 'last_msg'])

   data = dict(
      seq=msg.seq, body=body, sender_id=msg.sender.id,
   )

   def publish():
      channel_layer = get_channel_layer()
      group = f'user-{recipient_id}-{conv.id}'

      async_to_sync(channel_layer.group_send)(
         group,
         dict(type='message', data=data)
      )
      print(f'[*] 推送消息到 "{group}", {msg.id}')

   transaction.on_commit(publish)
   return data
