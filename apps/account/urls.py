from django.urls import path

from apps.account import views

app_name = 'account'

urlpatterns = [
    path('athlete', views.AthleteView.as_view(), name='athlete'),
    path('logout', views.LogOutView.as_view(), name='logout'),
]
