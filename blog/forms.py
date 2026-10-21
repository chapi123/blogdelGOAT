from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Comment


User = get_user_model()
username_field = User._meta.get_field(User.USERNAME_FIELD)


class AccountForm(forms.Form):
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=username_field.max_length,
        validators=username_field.validators,
        widget=forms.TextInput(attrs={'autocomplete': 'username'}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


class CommentForm(ModelForm):
    content = forms.CharField(
        label='Contenido',
        max_length=500,
        widget=forms.Textarea(attrs={'maxlength': '500'}),
    )

    class Meta:
        model = Comment
        fields = ['content']