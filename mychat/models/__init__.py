import json
import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe

from mychat.utils import model_instance_subset

if settings.DEBUG:
   class SimpleCounter(models.Model):
      val = models.IntegerField()

def user_avatar_path(thumbnail):
   def inner(instance, filename):
      return os.path.join(
         "avatars",
         f'user_{instance.id}',
         filename
      )

   return inner

class FriendRequest(models.Model):
   requester = models.ForeignKey("User", related_name="+", on_delete=models.CASCADE)
   recipient = models.ForeignKey("User", related_name="+", on_delete=models.CASCADE)
   user_pair_id = models.CharField(max_length=150)

   class Status(models.TextChoices):
      PENDING = 'pending', '待确认'
      ACCEPTED = 'accepted', '已接受'
      REJECTED = 'rejected', '已拒绝'

   status = models.CharField(
      max_length=20,
      choices=Status.choices,
      default=Status.PENDING,
   )

class User(AbstractUser):
   avatar = models.ImageField(upload_to=user_avatar_path(thumbnail=False))
   avatar_thumbnail = models.ImageField(upload_to=user_avatar_path(thumbnail=True))
   display_name = models.CharField(max_length=150)
   unread_messages = models.IntegerField(default=0)
   unread_friend_requests = models.IntegerField(default=0)

class Message(models.Model):
   body = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   conv = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
   seq = models.BigIntegerField()
   sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

class Conversation(models.Model):
   user_pair_id = models.CharField(max_length=150, unique=True)
   last_seq = models.BigIntegerField(default=0)
   last_msg_preview = models.CharField(max_length=150)
   last_msg_date = models.DateTimeField(null=True)

class UserConvState(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   peer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   friend = models.ForeignKey('Friendship', on_delete=models.CASCADE, related_name='+')
   conv = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='+')
   last_read_seq = models.BigIntegerField(default=0)

   def render_to_client(self):
      if not 'conv' in self._state.fields_cache:
         raise RuntimeError("conv不存在，N+1警告")

      conv = self.conv
      last_msg_date = timezone.localtime(conv.last_msg_date).strftime('%H:%M')
      state = dict(
         conv_id=conv.id,
         last_read_seq=self.last_read_seq,
         last_msg_preview=conv.last_msg_preview,
         last_msg_date=last_msg_date,
         unread=conv.last_seq - self.last_read_seq,
      )
      if 'friend' in self._state.fields_cache:
         state.update(friend_id=self.friend_id)
      return state

class Friendship(models.Model):
   user = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      related_name="friends",
   )
   friend_user = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      related_name="+",
   )

   remark = models.CharField(max_length=100, blank=True)

   class Meta:
      constraints = [
         models.UniqueConstraint(
            fields=["user_id", "friend_user_id"],
            name="uniq_friendship"
         )
      ]

   def render_to_client(self):
      return dict(
         id = self.id,
         friend_user_id=self.friend_user_id,
         avatar_url=self.friend_user.avatar.url,
         remark=self.remark,
      )