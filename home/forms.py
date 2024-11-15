# forms.py

from django import forms
from .models import DroneSettings

class DroneSettingsForm(forms.ModelForm):
    class Meta:
        model = DroneSettings
        fields = ['starting_lat', 'starting_lon', 'speed_kmh', 'direction']
        widgets = {
            'starting_lat': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter starting latitude'
            }),
            'starting_lon': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter starting longitude'
            }),
            'speed_kmh': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter speed in km/h'
            }),
            'direction': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
