from django import forms
from .models import CustomGroup

class GroupForm(forms.ModelForm):
    class Meta:
        model = CustomGroup
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du groupe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du groupe'})
        }

