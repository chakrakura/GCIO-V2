from django import forms

from gcio.ui import CHECKBOX_CLASS, INPUT_CLASS
from modules.taxonomy.models import CountryRegion

from .models import Organization


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'logo', 'email', 'phone', 'country', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Acme Capital Partners'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'contact@company.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+1 555 000 0000'}),
            'country': forms.Select(attrs={'class': 'hidden'}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['logo'].required = False
        self.fields['email'].required = False
        self.fields['phone'].required = False
        self.fields['country'].required = False
        self.fields['country'].queryset = CountryRegion.objects.filter(is_active=True)
        self.fields['country'].empty_label = 'Select country or region'
