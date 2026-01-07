from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

def dj_iconify(collection, icon):
   url = reverse('iconify_svg', collection, icon)
   return mark_safe((
      f'<img src="{url}" />'
   ))

@register.simple_tag
def iconify(collection, icon):
    return dj_iconify(collection, icon)
