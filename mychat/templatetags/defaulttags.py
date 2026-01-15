import json

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from mychat.events import user_event

register = template.Library()

@register.simple_tag(takes_context=True)
def constants_to_client(context):
   user = context['user']
   user_event_constants = user_event.get_event_constants()
   constants = dict(
      userEventUrl=reverse('user-events', args=[user.id]),
      **user_event_constants,
   )
   return mark_safe("window.__mychatConstants = " + json.dumps(constants))

@register.simple_tag
def user_events_channel(userid):
   return mark_safe(user_event.get_channel_name(userid))

@register.simple_tag
def iconify_icon(spec, extra_classes=""):
   collection, icon = spec.split(':')
   html = '<span class="icon-[{collection}--{icon}] {extra_classes}"></span>' \
          .format(collection=collection, icon=icon, extra_classes=extra_classes)
   return mark_safe(html)
