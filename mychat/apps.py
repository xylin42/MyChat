from django.apps import AppConfig, apps
from django.db.models.signals import post_save
from django.dispatch import receiver

class MyChatConfig(AppConfig):
   name = 'mychat'

   def ready__(self):
      User = self.apps.get_model('auth.User')
      Account = self.get_model('Account')

      @receiver(post_save, sender=Account)
      def account_created(sender, instance, created, **kwargs):
         if not created:
            return
         instance.set_password('123456')
         instance.save()