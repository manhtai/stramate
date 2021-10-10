from django.contrib import admin
from apps.activity.models import Activity


@admin.register(Activity)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'start_date', 'user']