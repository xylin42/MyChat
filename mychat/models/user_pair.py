def get_model_instance(model, id1, id2):
   return model.objects.get(user_pair_id=make_user_pair_id(id1, id2))

def make_user_pair_id(id1, id2):
   user_pair = sorted([id1, id2])
   user_pair_id = '{0}-{1}'.format(*user_pair)
   return user_pair_id


def delete_model_instance(model, id1, id2):
   model.objects.filter(user_pair_id=make_user_pair_id(id1, id2)).delete()


def create_model_instance(model, *args, **kwargs):
   if args:
      if len(args) != 2:
         raise ValueError("user_pair kwargs 长度必须是2")
      pair = args
      kwargs = {}
   else:
      if len(kwargs) != 2:
         raise ValueError("user_pair kwargs 长度必须是2")
      pair = kwargs.values()

   return model.objects.create(user_pair_id=make_user_pair_id(*pair), **kwargs)

