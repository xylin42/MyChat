from django.apps import AppConfig
from django.contrib.auth import user_logged_in
from django.dispatch import receiver

class MyChatConfig(AppConfig):
   name = 'mychat'

   def ready(self):
      @receiver(user_logged_in)
      def user_logged_in_handler(user, request, **kwargs):
         with open('temp/auth_user_hash', 'at') as f:
            hash = request.session['_auth_user_hash']
            assert hash == user.get_session_auth_hash()
            password = user.password
            f.write(f"password: {password}\nhash: {hash}\n\n")