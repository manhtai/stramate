from django import forms
from django.forms.widgets import Textarea, TextInput, NumberInput
from apps.activity.models import Activity


class ActivityForm(forms.ModelForm):
    name = forms.Field(widget=TextInput(attrs={'class': "form-control form-block"}))
    description = forms.Field(
        required=False,
        widget=Textarea(attrs={'class': "form-control form-block"}),
    )
    initial_rotation = forms.IntegerField(
        widget=NumberInput(attrs={'class': "form-control form-block"}),
    )

    class Meta:
        model = Activity
        fields = ['name', 'description', 'initial_rotation']
