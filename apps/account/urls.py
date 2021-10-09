from django.urls import path

from apps.account.views import ProfileView

app_name = 'account'

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
]
