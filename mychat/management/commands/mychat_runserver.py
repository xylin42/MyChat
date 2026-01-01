import os

from django.contrib.auth.hashers import make_password, get_hasher
from django.core.files.base import ContentFile
from django.core.management import BaseCommand, call_command

from mychat.models import Contact, User


def default_avatar_file():
   bs = open('data/default-avatar', 'rb').read()
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

def insert_users_data():
   password = make_password('123456', fixed_salt())
   for i in range(1,5):
      x = User.objects.create(
         username=f'user{i}',
         display_name=f"用户{i}",
         password=password,
         avatar=default_avatar_file(),
      )

def insert_contacts_data():
   for i in range(1,4):
      x = Contact.objects.create(
         user_id=1,
         contact_id=i,
         remark=f'朋友{i}'
      )

def test_channels_layer():
   import channels.layers
   from asgiref.sync import async_to_sync

   channel_layer = channels.layers.get_channel_layer()
   async_to_sync(channel_layer.send)('test_channel', dict(type='hello'))
   x = async_to_sync(channel_layer.receive)('test_channel')
   assert x == dict(type='hello')

class Command(BaseCommand):
   def handle(self, *args, **options):
      if os.environ.get('RUN_MAIN') != 'true':
         call_command('migrate_mychat')

         insert_users_data()
         insert_contacts_data()

         #test_channels_layer()

      call_command('runserver')
