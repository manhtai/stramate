from django import forms
from django.forms.widgets import DateInput, NumberInput, Select

from apps.account.models import Athlete


class AthleteForm(forms.ModelForm):
    birthday = forms.DateField(widget=DateInput(attrs={'class': "form-control form-block"}))

    sex = forms.ChoiceField(
        widget=Select(attrs={'class': "form-control form-block"}),
        choices=(("O", "Other"), ("M", "Male"), ("F", "Female")),
    )
    resting_hr = forms.IntegerField(widget=NumberInput(attrs={'class': "form-control form-block"}))

    class Meta:
        model = Athlete
        fields = [
            'sex',
            'birthday',
            'resting_hr',
        ]
