from django.urls import path

from apps.page.views import IndexView

app_name = 'page'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
