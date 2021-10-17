from django.contrib import admin
from apps.account.models import Athlete


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user']
