from django_eventstream import send_event

channels_format = 'users/{userid}/events'
urlpattern = 'users/<userid>/events'

def get_channel_name(userid):
   return channels_format.format(userid=userid)

def get_publish_func(userid, event_type, data=None):
   def publish():
      channel = get_channel_name(userid)
      send_event(channel, event_type, data or {})
      print(f'[*] 推送事件到 "{channel}", 类型="{event_type}"')

   return publish