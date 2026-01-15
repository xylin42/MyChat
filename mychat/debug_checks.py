from django.db import transaction
from django.db.models import F


SimpleCounter = None

def check_db_behavior():
   @transaction.atomic
   def inner1():
      SimpleCounter.objects.update(val=F('val')+1)
      x=1
   inner1()

def run_debug_checks(app):
   global SimpleCounter
   SimpleCounter = app.get_model('SimpleCounter')
   check_db_behavior()
