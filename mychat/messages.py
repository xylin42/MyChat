import hashlib

from django.db import transaction
from django.db.models import F

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
def send_message(conv_id, sender, receiver, message):
   if conv_id is None:
      conv = start_conversation(sender, receiver)
   else:
      conv = Conversation.objects.select_for_update().get(id=conv_id)
   conv.last_seq += 1

   msg = conv.messages.create(payload=message, conversation=conv, seq=conv.last_seq, sender=sender)
   conv.last_msg = msg
   conv.save(update_fields=['last_seq', 'last_msg'])

   return msg