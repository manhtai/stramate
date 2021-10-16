from django.urls import path

from apps.page.views import IndexView, ProfileView

app_name = 'page'

urlpatterns = [
    path('<username>', ProfileView.as_view(), name='profile'),
    path('', IndexView.as_view(), name='index'),
]
