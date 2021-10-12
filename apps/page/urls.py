from django.urls import path

from apps.page.views import IndexView, AthleteView

app_name = 'page'

urlpatterns = [
    path('<username>', AthleteView.as_view(), name='athlete'),
    path('', IndexView.as_view(), name='index'),
]
