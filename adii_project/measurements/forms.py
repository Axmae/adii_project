from django import forms
from .models import Measurement

FIELD_ATTRS = {'class': 'form-input', 'step': '0.5', 'min': '0'}

class MeasurementForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ['type_equipement', 'tour_poitrine', 'tour_taille', 'tour_hanches', 'epaules', 'manche', 'entrejambe']
        widgets = {
            'type_equipement': forms.Select(attrs={'class': 'form-input'}),
            'tour_poitrine': forms.NumberInput(attrs=FIELD_ATTRS),
            'tour_taille': forms.NumberInput(attrs=FIELD_ATTRS),
            'tour_hanches': forms.NumberInput(attrs=FIELD_ATTRS),
            'epaules': forms.NumberInput(attrs=FIELD_ATTRS),
            'manche': forms.NumberInput(attrs=FIELD_ATTRS),
            'entrejambe': forms.NumberInput(attrs=FIELD_ATTRS),
        }

class AdminNoteForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ['notes_admin']
        widgets = {'notes_admin': forms.Textarea(attrs={'class': 'form-input', 'rows': 3})}
