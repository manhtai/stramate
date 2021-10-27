from django.contrib import admin
from apps.activity.models import Activity, Analytic


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'start_date', 'user',
        'moving_time', 'distance', 'total_elevation_gain',
    ]
    search_fields = ['name', 'description', 'start_location']
    list_filter = ['start_date', 'type']


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'date', 'user']
    list_filter = ['date']
