from django import forms
from django.contrib.auth.models import User

from django.utils import timezone

from gcio.ui import CHECKBOX_CLASS, INPUT_CLASS, SELECT_CLASS, TEXTAREA_CLASS
from modules.organizations.models import Organization
from modules.taxonomy.models import AssetClass, CountryRegion, PublicationType, ReportTag

from .models import Report


class ReportForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role__is_internal=True),
        required=True,
        empty_label="Select author...",
        widget=forms.Select(attrs={'class': SELECT_CLASS, 'required': 'required'}),
    )
    published_at = forms.DateField(
        required=False,
        label="Publish Date",
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': INPUT_CLASS}
        )
    )

    class Meta:
        model = Report
        fields = [
            'content_type', 'title', 'description', 'body', 'file_upload',
            'status', 'access_level', 'published_at', 'visible_organizations', 'publication_type', 'page_count', 'is_featured',
            'author', 'asset_classes', 'countries_regions', 'tags',
        ]
        widgets = {
            'content_type': forms.RadioSelect,
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Editorial title...', 'required': 'required'}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4, 'placeholder': 'One or two sentences summarizing the report...', 'required': 'required'}),
            'body': forms.Textarea(attrs={'id': 'body-input', 'class': 'hidden'}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'access_level': forms.Select(attrs={'class': SELECT_CLASS}),
            'visible_organizations': forms.CheckboxSelectMultiple,
            'publication_type': forms.Select(attrs={'class': SELECT_CLASS, 'required': 'required'}),
            'page_count': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1, 'required': 'required'}),
            'is_featured': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'asset_classes': forms.CheckboxSelectMultiple,
            'countries_regions': forms.CheckboxSelectMultiple,
            'tags': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['author'].empty_label = "Select author..."
        self.fields['author'].required = True
        self.fields['publication_type'].queryset = PublicationType.objects.filter(is_active=True)
        self.fields['publication_type'].empty_label = "Select publication type..."
        self.fields['publication_type'].required = True
        self.fields['asset_classes'].queryset = AssetClass.objects.filter(is_active=True)
        self.fields['countries_regions'].queryset = CountryRegion.objects.filter(is_active=True)
        self.fields['tags'].queryset = ReportTag.objects.filter(is_active=True)
        self.fields['file_upload'].required = False

        if self.instance and self.instance.pk and self.instance.published_at:
            self.initial['published_at'] = self.instance.published_at.strftime('%Y-%m-%d')
        elif not self.initial.get('published_at'):
            self.initial['published_at'] = timezone.now().strftime('%Y-%m-%d')

        org_options = Organization.objects.filter(is_active=True)
        role = getattr(user, 'profile', None) and user.profile.role
        if user is not None and not (user.is_superuser or (role and role.can_view_all_organizations)):
            selected_ids = set()
            if self.instance and self.instance.pk:
                selected_ids = set(self.instance.visible_organizations.values_list('id', flat=True))
            allowed_ids = set(user.profile.organizations.values_list('id', flat=True)) | selected_ids
            org_options = org_options.filter(pk__in=allowed_ids)
        self.fields['visible_organizations'].queryset = org_options

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        file_upload = cleaned_data.get('file_upload')

        if not file_upload and self.instance and self.instance.pk and self.instance.file_upload:
            file_upload = self.instance.file_upload

        if content_type == Report.CONTENT_PDF:
            if not file_upload:
                self.add_error('file_upload', 'A PDF file is required for PDF reports.')
            else:
                name = file_upload.name.lower()
                if not name.endswith('.pdf'):
                    self.add_error('file_upload', 'Selected file format is invalid. PDF reports require a .pdf file.')
        elif content_type == Report.CONTENT_PRESENTATION:
            if not file_upload:
                self.add_error('file_upload', 'A presentation file (.pptx or .ppt) is required for Presentation reports.')
            else:
                name = file_upload.name.lower()
                if not (name.endswith('.pptx') or name.endswith('.ppt')):
                    self.add_error('file_upload', 'Selected file format is invalid. Presentation reports require a .pptx or .ppt file.')

        return cleaned_data
