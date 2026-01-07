import os

from django.contrib.auth.models import AbstractUser
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

class FriendRequest(models.Model):
   user1 = models.ForeignKey("User", related_name="+", on_delete=models.CASCADE)
   user2 = models.ForeignKey("User", related_name="+", on_delete=models.CASCADE)
   requester = models.ForeignKey("User", related_name="+", on_delete=models.CASCADE)

   status = models.CharField(
      choices=[
         ("pending", "Pending"),
         ("accepted", "Accepted"),
         ("rejected", "Rejected"),
         ("blocked", "Blocked"),
      ]
   )
   class Meta:
      constraints = [
         models.UniqueConstraint(
            fields=["user1", "user2"],
            name="uniq_friend_request"
         )
      ]


class User(AbstractUser):
   avatar = models.ImageField(upload_to=user_avatar_path(thumbnail=False))
   avatar_thumbnail = models.ImageField(upload_to=user_avatar_path(thumbnail=True))
   display_name = models.CharField(max_length=150)
   total_unread = models.IntegerField(default=0)

class Message(models.Model):
   body = models.TextField()
   created_at = models.DateTimeField(default=timezone.now)
   conv = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
   seq = models.BigIntegerField()
   sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

class Conversation(models.Model):
   user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   last_msg = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='+', null=True)
   last_seq = models.BigIntegerField(default=0)

   class Meta:
      constraints = [
         models.UniqueConstraint(
            fields=['user1', 'user2'],
            name='unique_conversation'
         )
      ]


class ConversationState(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   peer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
   friend = models.ForeignKey('Friendship', on_delete=models.CASCADE, related_name='+')
   conv = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='+')
   last_read_seq = models.BigIntegerField(default=0)

class Friendship(models.Model):
   user = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      related_name="friends",
   )
   friend = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      related_name="+",
   )

   remark = models.CharField(max_length=100, blank=True)

   class Meta:
      constraints = [
         models.UniqueConstraint(
            fields=["user", "friend"],
            name="uniq_friendship"
         )
      ]
