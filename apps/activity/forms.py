from django import forms
from django.forms.widgets import Textarea, TextInput, NumberInput, CheckboxInput
from apps.activity.models import Activity


class ActivityForm(forms.ModelForm):
    name = forms.Field(widget=TextInput(attrs={'class': "form-control form-block"}))
    description = forms.Field(
        required=False,
        widget=Textarea(attrs={'class': "form-control form-block"}),
    )
    initial_rotation = forms.IntegerField(
        required=False,
        widget=NumberInput(attrs={'class': "form-control form-block"}),
    )
    hide_map = forms.BooleanField(
        required=False,
        widget=CheckboxInput(attrs={'class': "form-control form-checkbox"}),
    )

    class Meta:
        model = Activity
        fields = ['name', 'description', 'hide_map', 'initial_rotation']
