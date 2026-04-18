from django import forms
from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['display_name', 'first_name', 'last_name', 'bio', 'website']
        widgets = {
            'display_name':    forms.TextInput(attrs={'placeholder': 'How you want to be called'}),
            'first_name':      forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name':       forms.TextInput(attrs={'placeholder': 'Last name'}),
            'bio':             forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short bio or tagline'}),
            'website':         forms.URLInput(attrs={'placeholder': 'https://yoursite.com'}),
        }