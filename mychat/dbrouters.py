class SimpleRouter:
   contrib_apps = [
      'auth',
      'contenttypes',
      'sessions',
      'admin',
      'messages',
      'staticfiles'
   ]

   def route(self, model):
      if model._meta.app_label in self.contrib_apps:
         return "contrib"
      return "default"

   def db_for_read(self, model, **hints):
      return self.route(model)

   def db_for_write(self, model, **hints):
      return self.route(model)

   def allow_migrate(self, db, app_label, model_name=None, **hints):
      if app_label in self.contrib_apps:
         return db == "contrib"
      return db == "default"
