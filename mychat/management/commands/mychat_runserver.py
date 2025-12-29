import os
import shutil

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand, call_command
from django.db import connection

from mychat.models import Contact, User

def default_avatar_file():
   bs = open('data/default-avatar', 'rb').read()
   return ContentFile(bs, 'avatar')

def insert_users_data():
   for i in range(1,5):
      x = User.objects.create(
         username=f'user{i}',
         display_name=f"用户{i}"
      )
      x.avatar = default_avatar_file()
      x.set_password('123456')
      x.save()

def insert_contacts_data():
   for i in range(1,4):
      x = Contact.objects.create(
         user_id=1,
         contact_id=i,
         remark=f'朋友{i}'
      )

class Command(BaseCommand):
   def handle(self, *args, **options):
      if os.environ.get('RUN_MAIN') != 'true':
         call_command('migrate_mychat')

         insert_users_data()
         insert_contacts_data()

      call_command('runserver')
