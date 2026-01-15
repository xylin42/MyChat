import json
from urllib.parse import urlsplit, urlunsplit

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
from django.http import HttpResponse, QueryDict
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, include
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, DetailView, FormView
from django.views.generic.edit import BaseFormView

from .events import user_event
from .models import Friendship, User, UserConvState, FriendRequest
from .services.conversation import send_message, UserConvListCache
from .services.friendship import send_friend_request
from .services.user_state import UserStateCache


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
      base_layout = 'mychat/layouts/base'
      page_layout = f'mychat/layouts/base_{self.page_layout_type}'

      if self.is_htmx:
         base_layout += '_content'

         target = self.request.META.get('HTTP_HX_TARGET')
         if target != 'body-content':
            page_layout += '_content'


      if base_layout:
         context['base_layout'] = base_layout + '.html'

      context['back_url'] = self.get_back_url()
      context['page_layout'] = page_layout + '.html'
      context['is_htmx'] = self.is_htmx

      return context

class Logout(HtmxMixin, LogoutView):
   template_name = 'logged_out.html'

   def get_success_url(self):
      return '/'


class Login(HtmxMixin, LoginView):
   template_name = 'mychat/auth/login.html'

   def get_success_url(self):
      return "/"

   def get_form_kwargs(self):
      kwargs = super().get_form_kwargs()
      kwargs['renderer'] = FormRenderer()
      return kwargs


class UserStateMixin:
   def get_context_data(self):
      context = super().get_context_data()
      state = UserStateCache(self.request.user.id).get()
      context['user_state'] = state
      return context

class FriendRequestUpdateView(View):
   form = forms.modelform_factory(FriendRequest, fields=['status'])

   def patch(self, request, pk, **kwarg):
      data = QueryDict(request.body, encoding=request.encoding)
      form = self.form(data)
      if form.is_valid():
         FriendRequest.objects.filter(pk=pk).update(
            **form.cleaned_data
         )
      else:
         pass


class FriendRequestsListView(HtmxMixin, UserStateMixin, ListView):
   page_layout_type = 'stack'
   template_name = 'mychat/stacks/friend_requests.html'
   model = FriendRequest
   context_object_name = 'friend_requests'
   default_back_url = '/friends'

   def get_queryset(self):
      return self.model.objects.filter(recipient_id = self.request.user.id).select_related('requester')

class FriendListView(HtmxMixin,
                     UserStateMixin,
                     ListView):
   page_layout_type = 'shell'
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


class ConversationListView(HtmxMixin,
                           TemplateView):
   page_layout_type = 'shell'
   template_name = 'mychat/pages/conversations.html'
   cookie_last_updated_at = 'conv_list_last_updated_at'

   def render_to_response(self, context, **response_kwargs):
      resp = super().render_to_response(context, **response_kwargs)
      # resp.set_cookie(self.cookie_last_updated_at, self.last_updated_at)
      return resp

   def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      since = self.request.COOKIES.get(self.cookie_last_updated_at, None)
      cache = UserConvListCache(self.request.user.id)
      if not since:
         states, friends, last_updated_at = cache.reload_all()
         self.last_updated_at = last_updated_at
         context['full_states'] = zip(states, friends)
         context['states'] = states
         context['friends'] = friends
         context['is_full'] = True
         return context
      objs, last_updated_at = cache.get()
      self.last_updated_at = last_updated_at
      return list(objs)




class ConversationDetailView(DetailView):
   model = UserConvState
   context_object_name = 'state'
   template_name = 'mychat/stacks/conversation.html'

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


class UserProfileView(HtmxMixin, DetailView):
   model = User
   template_name = 'mychat/stacks/user_profile.html'
   context_object_name = 'target_user'

class CreateFriendRequestView(BaseFormView):
   class Form(forms.Form):
      requester = forms.IntegerField()
      recipient = forms.IntegerField()
   form_class = Form

   def form_valid(self, form):
      try:
         send_friend_request(**form.cleaned_data)
         return HttpResponse()
      except IntegrityError:
         return HttpResponse(status=409)

import django_eventstream.views

urlpatterns = [
   path('friend-requests', FriendRequestsListView.as_view()),
   path('friend-requests/<int:pk>', FriendRequestUpdateView.as_view()),
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
