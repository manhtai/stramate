from django.contrib import admin
from apps.activity.models import Activity, Analytic


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'start_date', 'user']
    search_fields = ['name']
    list_filter = ['start_date', 'type']


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'date', 'user']
    list_filter = ['date']
