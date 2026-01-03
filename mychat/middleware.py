from django.shortcuts import redirect


class LoginRequiredMiddleware:
   def __init__(self, get_response):
      self.get_response = get_response

   def __call__(self, req):
      if not req.user.is_authenticated:
         if req.path == '/login':
            return self.get_response(req)

         return redirect('/login')

      if req.path == '/':
         return redirect('/conversations')

      return self.get_response(req)
