from django_eventstream import send_event
from django_eventstream.utils import get_storage

channels_format = 'users/{userid}/events'
urlpattern = 'users/<userid>/events'

USER_EVENT_NEW_MESSAGE = 'new-message'

def get_event_constants():
   return {key: value for key, value in globals().items() if key.startswith("USER_EVENT")}

def get_channel_name(userid):
   return channels_format.format(userid=userid)

def publish_new_message(userid, data):
   publish_event(userid, USER_EVENT_NEW_MESSAGE, data)

def publish_event(userid, event_type, payload=None):
   channel = get_channel_name(userid)
   data = {
      'type': event_type,
      'payload': payload
   }
   ev = send_event(channel, "", data)
   id = get_storage().get_current_id(channel)
   print(f'[*] 推送事件到 "{channel}", 类型="{event_type}", id={id}')
