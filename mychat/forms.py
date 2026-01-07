from django import forms
from .models import User

class UniqueUserPairForm(forms.Form):
   user1 = forms.IntegerField()
   user2 = forms.IntegerField()

class BaseProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []

class AvatarForm(BaseProfileForm):
    class Meta(BaseProfileForm.Meta):
        fields = ["avatar"]

class DisplayNameForm(BaseProfileForm):
    class Meta(BaseProfileForm.Meta):
        fields = ["display_name"]

class ProfileForm(BaseProfileForm):
    class Meta(BaseProfileForm.Meta):
        fields = ["display_name", "avatar"]
