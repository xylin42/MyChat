import os

from channels.layers import get_channel_layer
from django.contrib.auth.hashers import make_password, get_hasher
from django.core.files.base import ContentFile
from django.core.management import BaseCommand, call_command

from mychat.messages import send_message, start_conversation
from mychat.models import Contact, User, Message, Conversation


def avatar_yelling_cat():
   bs = open('data/yellingcat@192.webp', 'rb').read()
   return ContentFile(bs, 'avatar')

def avatar_yelling_woman():
   bs = open('data/yellingwoman@192.webp', 'rb').read()
   return ContentFile(bs, 'avatar')

def fixed_salt():
   path = 'data/salt'
   if os.path.exists(path):
      with open('data/salt', 'rt') as f:
         salt = f.read()
         if salt:
            return salt
   with open(path, 'wt') as f:
      salt = get_hasher('default').salt()
      f.write(salt)
      return salt

def insert_messages():
   user = User.objects.get(pk=1)
   for i in range(2,5):
      peer = User.objects.get(pk=i)
      conv, created = Conversation.objects.get_or_create_by_id_pair((user.id, peer.id))

      for j in range(3):
         send_message(conv.id, peer.id, user.id, f"[{j}] 你好，{user.display_name}")
         send_message(conv.id, user.id, peer.id, f'[{j}] 你好，{peer.display_name}')

      conv.refresh_from_db()
      assert conv.last_seq == 6

def insert_users_data():
   password = make_password('123456', fixed_salt())
   for i in range(1,5):
      avatar = avatar_yelling_cat() if i == 1 else avatar_yelling_woman()
      User.objects.create(
         username=f'user{i}',
         display_name=f"用户{i}",
         password=password,
         avatar=avatar,
      )

def insert_contacts_data():
   for i in range(1,4):
      x = Contact.objects.create(
         user_id=1,
         contact_id=i,
         remark=f'朋友{i}'
      )

def test_channels_layer():
   from asgiref.sync import async_to_sync

   channel_layer = get_channel_layer()

   async_to_sync(channel_layer.send)('test_channel', dict(type='hello'))
   x = async_to_sync(channel_layer.receive)('test_channel')

   assert x == dict(type='hello')

   #async_to_sync(channel_layer.flush)()


class Command(BaseCommand):
   def handle(self, *args, **options):
      if os.environ.get('RUN_MAIN') != 'true':
         call_command('migrate_mychat')

         insert_users_data()
         insert_contacts_data()
         insert_messages()

         test_channels_layer()

      call_command('runserver')
