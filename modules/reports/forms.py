from django import forms
from django.contrib.auth.models import User

from gcio.ui import CHECKBOX_CLASS, INPUT_CLASS
from modules.organizations.models import Organization
from modules.taxonomy.models import AssetClass, CountryRegion, PublicationType, ReportTag

from .models import Report


class ReportForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role__is_internal=True),
        required=False,
        widget=forms.RadioSelect,
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
            'title': forms.TextInput(attrs={
                'class': 'canvas-title-input w-full font-serif font-bold text-3xl sm:text-4xl text-gray-900 dark:text-gray-100 bg-transparent border-none focus:outline-none focus:ring-0 p-0 placeholder-gray-300 dark:placeholder-gray-600',
                'placeholder': 'Editorial title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'canvas-dek-input w-full italic text-lg text-gray-500 dark:text-gray-400 bg-transparent border-none focus:outline-none focus:ring-0 p-0 resize-none placeholder-gray-300 dark:placeholder-gray-600',
                'rows': 2,
                'placeholder': 'One or two sentences summarising the report. Shown on cards and above the article.',
            }),
            'body': forms.Textarea(attrs={'id': 'body-input', 'class': 'hidden'}),
            'status': forms.Select(attrs={'class': 'hidden'}),
            'access_level': forms.RadioSelect,
            'visible_organizations': forms.CheckboxSelectMultiple,
            'publication_type': forms.RadioSelect,
            'page_count': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1}),
            'is_featured': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'asset_classes': forms.CheckboxSelectMultiple,
            'countries_regions': forms.CheckboxSelectMultiple,
            'tags': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
        self.fields['description'].required = False
        self.fields['publication_type'].queryset = PublicationType.objects.filter(is_active=True)
        self.fields['publication_type'].required = False
        self.fields['asset_classes'].queryset = AssetClass.objects.filter(is_active=True)
        self.fields['countries_regions'].queryset = CountryRegion.objects.filter(is_active=True)
        self.fields['tags'].queryset = ReportTag.objects.filter(is_active=True)
        self.fields['file_upload'].required = False
        self.fields['page_count'].required = False

        org_options = Organization.objects.filter(is_active=True)
        role = getattr(user, 'profile', None) and user.profile.role
        if user is not None and not (user.is_superuser or (role and role.can_view_all_organizations)):
            selected_ids = set()
            if self.instance and self.instance.pk:
                selected_ids = set(self.instance.visible_organizations.values_list('id', flat=True))
            allowed_ids = set(user.profile.organizations.values_list('id', flat=True)) | selected_ids
            org_options = org_options.filter(pk__in=allowed_ids)
        self.fields['visible_organizations'].queryset = org_options

    def clean_page_count(self):
        # page_count is a non-nullable column — fall back to 1 rather than erroring
        # when the field is left blank (it's no longer a required field).
        return self.cleaned_data.get('page_count') or 1

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
