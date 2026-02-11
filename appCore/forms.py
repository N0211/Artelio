"""Forms for registration and profile editing."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import ArtistProfile, CustomUser

class UserRegistrationForm(UserCreationForm):
    """Signup form that collects email and role."""
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        """Persist the user with the provided email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ArtistProfileForm(forms.ModelForm):
    """Editable fields for an artist profile."""
    email = forms.EmailField(required=True)

    class Meta:
        model = ArtistProfile
        fields = ('phone', 'bio', 'website', 'profile_image')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['email'].initial = user.email
