import os

from django.core.asgi import get_asgi_application
from django.template.loader import render_to_string
from django.urls import re_path

from mychat.models import UserConvState

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mychat.settings')

class MyConsumer():
   async def connect(self):
      await self.accept()

      conv_id = self.scope['url_route']['kwargs']['conv_id']
      self.user = self.scope['user']
      self.peer = await self.get_peer(conv_id, self.user.id)
      group_name = f'user-{self.user.id}-{conv_id}'
      await self.channel_layer.group_add(group_name, self.channel_name)

      print(f'[*] 监听对话消息, "{group_name}"')

   async def get_peer(self, conv_id, user_id):
      state = await UserConvState.objects.select_related('peer').aget(user_id=user_id, conv_id=conv_id)
      return state.peer

   async def receive(self, text_data=None, bytes_data=None):
      pass

   async def dispatch(self, msg):
      print('[*] 新事件, msg=', msg)
      await super().dispatch(msg)

   async def message(self, event):
      data = event['data']
      ctx = dict(
         **data, sender_avatar_url = self.peer.avatar.url,
      )
      html = render_to_string('mychat/partials/message.html', ctx)
      await self.send(text_data=html)


application = get_asgi_application()
