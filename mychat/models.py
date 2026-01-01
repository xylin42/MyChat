import os
import uuid
from io import BytesIO

from PIL import Image, ImageOps
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

def user_avatar_path(thumbnail):
   def inner(instance, filename):
      return os.path.join(
         "avatars",
         f'user_{instance.id}',
         filename
      )
   return inner

def create_avatar_thumbnail(imgfile):
   img = Image.open(imgfile)
   img.thumbnail(
      (300, 300), Image.LANCZOS
   )
   buf = BytesIO()
   img.save(buf, format='JPEG', quality=85, optimize=True)
   return ContentFile(buf.getvalue(), "avatar_thumbnail.jpg")

def normalize_avatar(imgfile):
   img = Image.open(imgfile)
   img = ImageOps.exif_transpose(img)

   if img.mode not in ("RGB", "L"):
      img = img.convert("RGB")

   img.thumbnail((300,300), Image.LANCZOS)

   buf = BytesIO()
   img.save(buf, format="JPEG", quality=85, optimize=True)
   return ContentFile(buf.getvalue(), name="avatar.jpg")

class User(AbstractUser):
   avatar = models.ImageField(upload_to=user_avatar_path(thumbnail=False))
   avatar_thumbnail = models.ImageField(upload_to=user_avatar_path(thumbnail=True))
   display_name = models.CharField(max_length=150)
   remark = models.CharField(max_length=150, null=True)
   messages_unread_count = models.IntegerField(default=0)
   # inbox = models.ForeignKey("MessageInbox", on_delete=models.CASCADE)

   def save(self, *args, **kwargs):
      super().save(*args, **kwargs)
      avatar = self.avatar
      if avatar:
         avatar = normalize_avatar(avatar)
         self.avatar = avatar
         self.avatar_thumbnail = create_avatar_thumbnail(avatar)
         super().save()
         x=1

class Message(models.Model):
   # msg_type = models.IntegerField()
   payload = models.TextField()
   created_at = models.DateTimeField(default=timezone.now)
   conversation = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
   seq = models.BigIntegerField()
   sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')


class Conversation(models.Model):
   member1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   member2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   last_msg = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='+', null=True)
   uuid = models.UUIDField(default=uuid.uuid4)
   last_seq = models.BigIntegerField(default=0)

   def peer(self, me):
      if me.id == self.member1.id:
         return self.member2
      else:
         return self.member1

   def mark_read(self):
      self.update(
         read_at=timezone.now(),
         unread=0,
      )

class UserConvState(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   peer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   conv = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='+')
   last_read_seq = models.BigIntegerField(default=0)

   @property
   def unread(self):
      return self.conv.last_msg.seq - self.last_read_seq


class Contact(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    contact = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="related_to",
    )

    remark = models.CharField(max_length=100, blank=True)  # 备注名
    is_blocked = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(
       # auto_now_add=True
       default=timezone.now,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "contact"],
                name="uniq_user_contact"
            )
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.contact_id}"
