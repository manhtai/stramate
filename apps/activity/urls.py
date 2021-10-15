from django.urls import path

from apps.activity import views

app_name = 'activity'

urlpatterns = [
    path('<int:activity_id>/route', views.RouteView.as_view(), name='route'),
    path('<int:activity_id>', views.DetailView.as_view(), name='detail'),
]
