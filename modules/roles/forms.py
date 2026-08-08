from django import forms

from gcio.ui import CHECKBOX_CLASS, INPUT_CLASS, SELECT_CLASS, TEXTAREA_CLASS

from .models import Role


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            'name', 'description', 'color', 'is_internal',
            'can_manage_users', 'can_manage_roles', 'can_manage_organizations',
            'can_manage_content', 'can_manage_taxonomy', 'can_view_logs', 'can_view_all_organizations',
            'can_manage_market_data',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'color': forms.Select(attrs={'class': SELECT_CLASS}),
            'is_internal': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_manage_users': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_manage_roles': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_manage_organizations': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_manage_content': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_manage_taxonomy': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_view_logs': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_view_all_organizations': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_manage_market_data': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.is_system:
            self.fields['name'].disabled = True
