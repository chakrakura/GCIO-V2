import secrets
import string

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

from gcio.ui import INPUT_CLASS
from modules.organizations.models import Organization
from modules.roles.models import Role

from .models import Profile


def generate_temp_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))


class UserForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': INPUT_CLASS}))
    password = forms.CharField(
        max_length=128, required=False,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'autocomplete': 'new-password'}, render_value=False)
    )
    photo = forms.ImageField(required=False)
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.all(), required=False,
        widget=forms.SelectMultiple(attrs={'class': 'hidden'})
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all().order_by('name'), empty_label='Select role',
        widget=forms.Select(attrs={'class': 'hidden'})
    )

    def __init__(self, *args, editing_user=None, **kwargs):
        self.editing_user = editing_user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.editing_user:
            qs = qs.exclude(pk=self.editing_user.pk)
        if qs.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self):
        data = self.cleaned_data
        temp_password = None
        if self.editing_user:
            user = self.editing_user
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            if data.get('password'):
                user.set_password(data['password'])
        else:
            username = data['email'].split('@')[0] + '-' + secrets.token_hex(2)
            user = User(username=username, email=data['email'], first_name=data['first_name'], last_name=data['last_name'])
            if data.get('password'):
                user.set_password(data['password'])
            else:
                temp_password = generate_temp_password()
                user.set_password(temp_password)
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = data['role']
        if data.get('photo'):
            profile.photo = data['photo']
        profile.save()
        profile.organizations.set(data['organizations'])

        return user, temp_password


class ProfileSelfForm(forms.Form):
    """Self-service profile edit — only the fields a user may change about themselves.

    Email is intentionally excluded: it's the account's login identifier, provisioned by
    GCIO staff, so self-service changes go through support rather than this form.
    """
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    photo = forms.ImageField(required=False)

    def __init__(self, *args, editing_user=None, **kwargs):
        self.editing_user = editing_user
        super().__init__(*args, **kwargs)

    def save(self):
        data = self.cleaned_data
        user = self.editing_user
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        if data.get('photo'):
            profile.photo = data['photo']
            profile.save()

        return user


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASS
