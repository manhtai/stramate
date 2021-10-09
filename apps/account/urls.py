from django.urls import path

from apps.account import views

app_name = 'account'

urlpatterns = [
    path('profile', views.ProfileView.as_view(), name='profile'),
    path('logout', views.LogOutView.as_view(), name='profile'),
]
