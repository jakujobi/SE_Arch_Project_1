from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']  # Ensure email is stored in the User model
        if commit:
            user.save()
            # Create a Profile instance without storing the email
            Profile.objects.create(user=user)
        return user

class ProfileForm(forms.ModelForm):
    username = forms.CharField(required=True, help_text="Required")
    first_name = forms.CharField(required=True, help_text="Required")
    last_name = forms.CharField(required=True, help_text="Required")
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")

    class Meta:
        model = Profile
        fields = ['username', 'first_name', 'last_name', 'email']