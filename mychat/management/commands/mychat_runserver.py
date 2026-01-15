import os
import shutil
import threading
import time
from pathlib import Path

from django.contrib.auth.hashers import make_password, get_hasher
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.db.models import F
from django.urls import resolve

from mychat.events import user_event
from mychat.models import Friendship, User, SimpleCounter
from mychat.services import user_state
from mychat.services.conversation import create_unique_conversation, send_message
from mychat.utils import image_to_jpeg


def wizards_jpeg():
   try:
      shutil.rmtree('data/wizards_jpeg')
   except FileNotFoundError:
      pass
   dstdir = Path('data/wizards_jpeg')
   dstdir.mkdir()
   srcdir = Path('data/wizards')
   for p in srcdir.iterdir():
      dstpath = dstdir / p.name
      with dstpath.open('wb') as f:
         bs = image_to_jpeg(p)
         f.write(bs.getvalue())

def wizard_avatar(i):
   if i > 4:
      i -= 4
   bs = open(f'data/wizards_jpeg/wizard_{i}.png', 'rb').read()
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
      conv = create_unique_conversation(user.id, peer.id)

      for j in range(3):
         send_message(conv.id, peer.id, user.id, f"[{j}] 你好，{user.display_name}")
         # send_message(conv.id, user.id, peer.id, f'[{j}] 你好，{peer.display_name}')

      # conv.refresh_from_db()
      # assert conv.last_seq == 6

def insert_users_data():
   password = make_password('123456', fixed_salt())
   for i in range(1, 6):
      avatar = wizard_avatar(i)
      User.objects.create(
         username=f'user{i}',
         display_name=f"用户{i}",
         password=password,
         avatar=avatar,
      )

def insert_friends_data():
   for i in range(2, 5):
      Friendship.objects.create(user_id=1, friend_user_id=i, remark=f'朋友{i}')
      Friendship.objects.create(user_id=i, friend_user_id=1, remark=f'朋友{i}')

def check_db_behavior():
   @transaction.atomic
   def target1():
      SimpleCounter.objects.update(val=F('val')+1)
      t1_event1.set()
      t1_event2.wait()

   @transaction.atomic
   def target2():
      t1_event1.wait()
      SimpleCounter.objects.update(val=F('val') + 1)
      t2_event1.set()

   def join_thread(thread):
      thread.join(2)
      return not thread.is_alive()

   t1_event1 = threading.Event()
   t1_event2 = threading.Event()
   t2_event1 = threading.Event()
   t1 = threading.Thread(target=target1)
   t2 = threading.Thread(target=target2)
   t1.start()
   t2.start()

   t1_event1.wait()
   assert not t2_event1.wait(2), "[E] 线程2没有被阻塞"

   t1_event2.set()
   assert join_thread(t1), '[E] 线程1没有完成执行'
   assert join_thread(t2), '[E] 线程2没有完成执行'



class Command(BaseCommand):
   def handle(self, *args, **options):
      if os.environ.get('RUN_MAIN') != 'true':
         call_command('migrate_mychat')

         # check_db_behavior()
         call_command('migrate', 'django_eventstream', '--database=default')

         wizards_jpeg()

         insert_users_data()
         insert_friends_data()
         insert_messages()


      call_command('runserver')
