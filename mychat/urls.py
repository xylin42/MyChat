import asyncio
import json
import time

from channels.generic.http import AsyncHttpConsumer
from django import forms
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.forms import BoundField
from django.forms.renderers import DjangoTemplates
from django.forms.widgets import Input
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, include
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, DetailView, CreateView, FormView

from .messages import send_message
from .models import Contact, User, Conversation, Message, UserConvState


@login_required
def index(req):
   return render(req, 'index.html')

class BoundField(BoundField):
   def build_widget_attrs(self, attrs, widget=None):
      attrs = super().build_widget_attrs(attrs, widget)
      if isinstance(widget, Input):
         attrs.update({
            'class': 'text-lg pl-2'
         })
      return attrs

   def label_tag(self):
      return super().label_tag(attrs={
         'class': 'label',
      })

class FormRenderer(DjangoTemplates):
   form_template_name = 'form.html'
   bound_field_class = BoundField

class Logout(LogoutView):
   template_name = 'logged_out.html'
   def get_success_url(self):
      return '/'

class Login(LoginView):
   template_name = 'mychat/portal/portal_login.html'

   def get_success_url(self):
      return "/"

   def get_form_kwargs(self):
      kwargs = super().get_form_kwargs()
      kwargs['renderer'] = FormRenderer()
      return kwargs

@method_decorator(login_required, 'dispatch')
class ContactListView(ListView):
   template_name = 'mychat/app/contact_list.html'
   model = Contact

@method_decorator(login_required, "dispatch")
class AddContactView(TemplateView):
   template_name = 'mychat/app/add_contact.html'

class SleepMixin:
   def get(self, req, *args, **kwargs):
      time.sleep(3)
      return super().get(req, *args, **kwargs)

class UserListView(SleepMixin, ListView):
   model = User
   allow_empty = False

   def get_queryset(self):
      username = self.request.GET.get('username')
      if not username:
         return User.objects.none()
      return User.objects.filter(username__icontains=username)

class UserProfileView(LoginRequiredMixin, TemplateView):
   template_name = 'user_profile.html'

class EntryView(View):
   def get(self, req):
      if req.user.is_authenticated:
         return render(req, "mychat/app/index.html")
      return render(req, 'mychat/portal/portal.html')

class ConversationListView(ListView):
   template_name = 'mychat/app/conversations.html'
   context_object_name = 'states'

   def get_queryset(self):
      qs = (UserConvState.objects.filter(user_id=self.request.user.id)
            .select_related("conv", "conv__last_msg", "user", "peer"))
      return qs

   def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      context.update(
         total_unread=sum(state.unread for state in context['states'])
      )
      return context


class ConversationDetailView(DetailView):
   model = UserConvState
   context_object_name = 'state'
   template_name = 'mychat/popups/conversation.html'

   def get_object(self, queryset=None):
      return get_object_or_404(
         UserConvState, conv_id=self.kwargs['pk'], user_id=self.request.user.id,
      )

   def get_context_data(self, **kwargs):
      data = super().get_context_data(**kwargs)
      state = data['state']
      conv = state.conv
      messages = conv.messages.order_by('seq')
      data['messages'] = messages
      data['peer'] = state.peer
      return data

@method_decorator(csrf_exempt, 'dispatch')
class ConversationMessageCreateView(FormView):
   class _Form(forms.Form):
      recipient_id = forms.IntegerField()
      body = forms.CharField(max_length=150)

   form_class = _Form

   def form_valid(self, form):
      data = form.cleaned_data
      data['conv_id'] = self.kwargs['pk']
      data['sender_id'] = self.request.user.id

      context = send_message(**data)
      context['user'] = self.request.user
      res = render_to_string("mychat/partials/message.html", context)
      return HttpResponse(res)

# x=1
urlpatterns = [
   path("__reload__/", include("django_browser_reload.urls")),
   path("icons/", include("dj_iconify.urls")),

   path('', EntryView.as_view()),
   path('conversations', ConversationListView.as_view()),
   path('conversations/<int:pk>', ConversationDetailView.as_view()),
   path('conversations/<int:pk>/messages', ConversationMessageCreateView.as_view()),
   path('profile', UserProfileView.as_view()),
   path('contacts', ContactListView.as_view()),
   path('contacts/add', AddContactView.as_view()),
   path('users', UserListView.as_view()),
   path('login', Login.as_view()),
   path('logout', Logout.as_view()),
   path('admin', admin.site.urls)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
