from django import forms
from django.forms.widgets import DateInput, NumberInput

from apps.account.models import Athlete


class AthleteForm(forms.ModelForm):
    birthday = forms.DateField(widget=DateInput(attrs={'class': "form-control form-block"}))

    hr_zone_threshold_1 = forms.FloatField(widget=NumberInput(attrs={'class': "form-control form-block"}))
    hr_zone_threshold_2 = forms.FloatField(widget=NumberInput(attrs={'class': "form-control form-block"}))
    hr_zone_threshold_3 = forms.FloatField(widget=NumberInput(attrs={'class': "form-control form-block"}))
    hr_zone_threshold_4 = forms.FloatField(widget=NumberInput(attrs={'class': "form-control form-block"}))

    class Meta:
        model = Athlete
        fields = [
            'birthday',
            'hr_zone_threshold_1', 'hr_zone_threshold_2', 'hr_zone_threshold_3', 'hr_zone_threshold_4',
        ]
