import json
import time
from urllib.parse import urlparse, urlsplit, urlunsplit

import django_eventstream
from django import forms
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError
from django.forms import BoundField
from django.forms.renderers import DjangoTemplates
from django.forms.widgets import Input
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, include, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, DetailView, FormView, CreateView
from django.views.generic.edit import FormMixin, ProcessFormView, BaseFormView

from .events import user_event
from .forms import UniqueUserPairForm
from .models import Friendship, User, ConversationState, FriendRequest
from .services.conversation import send_message
from .services.friendship import send_friend_request


@login_required
def index(req):
   return render(req, 'index.html')


class BoundField(BoundField):
   def build_widget_attrs(self, attrs, widget=None):
      attrs = super().build_widget_attrs(attrs, widget)
      if isinstance(widget, Input):
         attrs.update({
            'class': 'input input-neutral'
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
   template_name = 'mychat/auth/login.html'

   def get_success_url(self):
      return "/"

   def get_form_kwargs(self):
      kwargs = super().get_form_kwargs()
      kwargs['renderer'] = FormRenderer()
      return kwargs


class HtmxMixin:
   def dispatch(self, request, *args, **kwargs):
      self.is_htmx = request.META.get('HTTP_HX_REQUEST') == 'true'
      return super().dispatch(request, *args, **kwargs)

   def get_back_url(self):
      if not self.is_htmx:
         return getattr(self, 'default_back_url', '')

      url = self.request.META.get('HTTP_HX_CURRENT_URL')
      p = urlsplit(url)
      return urlunsplit(('', '', p.path, p.query, p.fragment))

   def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      url_name = self.request.resolver_match.url_name
      base_layout = 'mychat/layouts/base'
      page_layout = ''
      if url_name in ('conversation-list', 'contact-list', 'profile'):
         page_layout = 'mychat/layouts/base_shell'
      elif url_name in ('search-user', 'user-profile'):
         page_layout = 'mychat/layouts/base_stack'
      if self.is_htmx:
         base_layout += '_content'
         target = self.request.META.get('HTTP_HX_TARGET')
         if target != 'body-content':
            page_layout += '_content'
         context['back_url'] = self.get_back_url()
      if not page_layout:
         raise Exception('PageLayoutMixin错误')
      base_layout += '.html'
      page_layout += '.html'
      context['base_layout'] = base_layout
      context['page_layout'] = page_layout
      return context


class FriendListView(HtmxMixin, ListView):
   template_name = 'mychat/pages/friends.html'
   model = Friendship
   context_object_name = 'friends'

   def get_queryset(self):
      return self.model.objects.filter(user_id=self.request.user.id).select_related('friend')


class AddFriendView(HtmxMixin, TemplateView):
   template_name = 'mychat/stacks/add_contact.html'

   def post(self):
      target_userid = int(self.request.POST.get('target_userid'))
      send_friend_request(self.request.user.id, target_userid)


class UserSearchView(HtmxMixin, TemplateView):
   template_name = 'mychat/stacks/search_user.html'
   default_back_url = '/friends'

   def get(self, request):
      target_username = request.GET.get('username')
      if target_username and self.is_htmx:
         target_user = get_object_or_404(User, username=target_username)
         #time.sleep(4)

         redirect = json.dumps(dict(path=f'/users/{target_user.id}/profile', target='#body-content'))
         resp = HttpResponse(headers={
            'HX-Location': redirect,
         })
         return resp
      return super().get(request)


class UserProfileView(LoginRequiredMixin, TemplateView):
   template_name = 'user_profile.html'


class EntryView(View):
   def get(self, req):
      if req.user.is_authenticated:
         return render(req, "mychat/app/index.html")
      return render(req, 'mychat/portal/portal.html')


class ConversationListView(HtmxMixin, ListView):
   template_name = 'mychat/pages/conversations.html'
   context_object_name = 'states'

   def get_queryset(self):
      qs = (ConversationState.objects.filter(user_id=self.request.user.id)
            .select_related("conv", "conv__last_msg", "user", "peer", "friend"))
      return qs

   def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      context.update(
         total_unread=12
      )
      return context


class ConversationDetailView(DetailView):
   model = ConversationState
   context_object_name = 'state'
   template_name = 'mychat/stacks/conversation.html'

   def get_object(self, queryset=None):
      return get_object_or_404(
         ConversationState, conv_id=self.kwargs['pk'], user_id=self.request.user.id,
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


class UserProfileView(HtmxMixin, DetailView):
   model = User
   template_name = 'mychat/stacks/user_profile.html'
   context_object_name = 'target_user'

class CreateFriendRequestView(BaseFormView):
   form_class = UniqueUserPairForm

   def form_valid(self, form):
      try:
         send_friend_request(**form.cleaned_data)
         return HttpResponse()
      except IntegrityError:
         return HttpResponse(status=409)

import django_eventstream.views

urlpatterns = [
   path('friend-requests/create', CreateFriendRequestView.as_view()),
   path(user_event.urlpattern, (django_eventstream.views.events), kwargs = {
      'format-channels': [user_event.channels_format]
   }, name='user-events'),
   path("__reload__/", include("django_browser_reload.urls")),

   path('', EntryView.as_view()),
   path('conversations', ConversationListView.as_view(), name='conversation-list'),
   path('conversations/<int:pk>', ConversationDetailView.as_view(), name='conversation-detail'),
   path('conversations/<int:pk>/messages', ConversationMessageCreateView.as_view()),
   path('conversations/<int:pk>/message-stream', include(django_eventstream.urls), {
      'format-channels': ['stream-{pk}']
   }),
   path('profile', UserProfileView.as_view()),
   path('friends', FriendListView.as_view(), name='contact-list'),
   path('friends/add', AddFriendView.as_view(), name='add-contact'),
   path('users/search', UserSearchView.as_view(), name='search-user'),
   path('users/<int:pk>/profile', UserProfileView.as_view(), name='user-profile'),
   path('login', Login.as_view()),
   path('logout', Logout.as_view()),
   path('admin', admin.site.urls)
]

static_urls = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static_urls

#assert reverse('user-events', kwargs=dict(userid=1)) == user_event.channels_format.format(userid=1)
