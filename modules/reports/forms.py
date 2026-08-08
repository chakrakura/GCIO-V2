from django import forms
from django.contrib.auth.models import User

from gcio.ui import CHECKBOX_CLASS, INPUT_CLASS, SELECT_CLASS, TEXTAREA_CLASS
from modules.organizations.models import Organization
from modules.taxonomy.models import AssetClass, CountryRegion, PublicationType, ReportTag

from .models import Report


class ReportForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role__is_internal=True),
        required=False, widget=forms.RadioSelect,
    )

    class Meta:
        model = Report
        fields = [
            'content_type', 'title', 'description', 'body', 'file_upload',
            'status', 'access_level', 'visible_organizations', 'publication_type', 'page_count', 'is_featured',
            'author', 'asset_classes', 'countries_regions', 'tags',
        ]
        widgets = {
            'content_type': forms.RadioSelect,
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Editorial title...'}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2, 'placeholder': 'One or two sentences...'}),
            'body': forms.Textarea(attrs={'id': 'body-input', 'class': 'hidden'}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'access_level': forms.Select(attrs={'class': SELECT_CLASS}),
            'visible_organizations': forms.CheckboxSelectMultiple,
            'publication_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'page_count': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1}),
            'is_featured': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'asset_classes': forms.CheckboxSelectMultiple,
            'countries_regions': forms.CheckboxSelectMultiple,
            'tags': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['publication_type'].queryset = PublicationType.objects.filter(is_active=True)
        self.fields['publication_type'].required = False
        self.fields['asset_classes'].queryset = AssetClass.objects.filter(is_active=True)
        self.fields['countries_regions'].queryset = CountryRegion.objects.filter(is_active=True)
        self.fields['tags'].queryset = ReportTag.objects.filter(is_active=True)
        self.fields['file_upload'].required = False

        org_options = Organization.objects.filter(is_active=True)
        role = getattr(user, 'profile', None) and user.profile.role
        if user is not None and not (user.is_superuser or (role and role.can_view_all_organizations)):
            selected_ids = set()
            if self.instance and self.instance.pk:
                selected_ids = set(self.instance.visible_organizations.values_list('id', flat=True))
            allowed_ids = set(user.profile.organizations.values_list('id', flat=True)) | selected_ids
            org_options = org_options.filter(pk__in=allowed_ids)
        self.fields['visible_organizations'].queryset = org_options
