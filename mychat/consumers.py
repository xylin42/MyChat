import asyncio
import json

from channels.generic.http import AsyncHttpConsumer


class MyConsumer(AsyncHttpConsumer):
   async def handle(self, body):
      user = self.scope['user']
      self.group_name = f'user:{user.id}'
      await self.channel_layer.group_add(self.group_name, self.channel_name)
      await self.send_headers(headers=[
         (b'content-type', b'text/event-stream'),
         (b'cache-control', b'no-cache'),
         (b'connection', b'keep-alive'),
      ])
      self.closed = False
      while not self.closed:
         await asyncio.sleep(60)
         await self.send_body(b': ping\n\n', more_body=True)

   async def notify(self, event):
      data = json.dumps(event['payload'], ensure_ascii=False).encode('utf-8')

      chunk = b'event: message\ndata: ' + data + b'\n\n'
      await self.send_body(chunk, more_body=True)
