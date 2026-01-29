from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Appointment

class SimpleRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help text
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service', 'package', 'preferred_date', 'preferred_time', 'notes']
        widgets = {
            'service': forms.Select(attrs={
                'class': 'form-control',
            }),
            'package': forms.Select(attrs={
                'class': 'form-control',
            }),
            'preferred_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'preferred_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Any special requests or notes...',
                'rows': 3,
                'required': False
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make both service and package optional initially
        self.fields['service'].required = False
        self.fields['package'].required = False
        # Filter only active services and packages
        self.fields['service'].queryset = self.fields['service'].queryset.filter(is_active=True)
        self.fields['package'].queryset = self.fields['package'].queryset.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        package = cleaned_data.get('package')
        
        # Ensure at least one is selected
        if not service and not package:
            raise forms.ValidationError('Please select either a Service or a Package.')
        
        return cleaned_data