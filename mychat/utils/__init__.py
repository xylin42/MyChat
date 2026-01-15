from io import BytesIO

from PIL import Image, ImageOps
from django.db import models

def model_instance_subset(d, *keys):
   r = {}
   for key in keys:
      if callable(key):
         key, val = key(d)
      else:
         val = getattr(d, key)
      r[key] = val
   return r

def image_to_jpeg(imgfile):
   img = Image.open(imgfile)
   img = ImageOps.exif_transpose(img)

   if img.mode not in ("RGB", "L"):
      img = img.convert("RGB")

   img.thumbnail((300,300), Image.LANCZOS)

   buf = BytesIO()
   img.save(buf, format="JPEG", quality=85, optimize=True)
   return buf
   #return ContentFile(buf.getvalue(), name="avatar.jpg")

def create_decimal_field():
   return models.DecimalField(max_digits=12, decimal_places=2)
