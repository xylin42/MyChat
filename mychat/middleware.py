from django.shortcuts import redirect


class LoginRequiredMiddleware:
   def __init__(self, get_response):
      self.get_response = get_response

   def __call__(self, req):
      if req.path == '/':
         return self.get_response(req)

      if req.user.is_authenticated:
         return self.get_response(req)

      if req.path == '/login':
         return self.get_response(req)

      return redirect('/login')