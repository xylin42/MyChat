from django import template
from django.utils.safestring import mark_safe

from mychat.events import user_event

register = template.Library()

@register.simple_tag
def user_events_channel(userid):
   return mark_safe(user_event.get_channel_name(userid))

@register.simple_tag
def iconify_icon(spec, extra_classes=""):
   collection, icon = spec.split(':')
   html = '<span class="icon-[{collection}--{icon}] {extra_classes}"></span>' \
          .format(collection=collection, icon=icon, extra_classes=extra_classes)
   return mark_safe(html)
