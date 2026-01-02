import os
import uuid
from io import BytesIO

from PIL import Image, ImageOps
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.db import models, transaction
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

   def avatar_url(self):
      return self.avatar.url

   def save_old(self, *args, **kwargs):
      super().save(*args, **kwargs)
      avatar = self.avatar
      if avatar:
         avatar = normalize_avatar(avatar)
         self.avatar = avatar
         self.avatar_thumbnail = create_avatar_thumbnail(avatar)
         super().save()

class Message(models.Model):
   body = models.TextField()
   created_at = models.DateTimeField(default=timezone.now)
   conv = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
   seq = models.BigIntegerField()
   sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

class ConversationQuerySet(models.QuerySet):
   def get_or_create_by_id_pair(self, id_pair):
      with transaction.atomic():
         id_pair = sorted(id_pair)
         conv, created = self.get_or_create(user1_id=id_pair[0], user2_id=id_pair[1])
         if created:
            UserConvState.objects.create(conv_id=conv.id, user_id=id_pair[0], peer_id=id_pair[1])
            UserConvState.objects.create(conv_id=conv.id, user_id=id_pair[1], peer_id=id_pair[0])
         return conv, created

class Conversation(models.Model):
   user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   last_msg = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='+', null=True)
   last_seq = models.BigIntegerField(default=0)
   objects = models.Manager.from_queryset(ConversationQuerySet)()

   class Meta:
      constraints = [
         models.UniqueConstraint(
            fields=['user1', 'user2'],
            name='unique_conversation_pair'
         )
      ]

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
