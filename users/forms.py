from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import User, Profile

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name', 'role')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user',)