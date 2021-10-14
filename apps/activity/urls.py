from django.urls import path

from apps.activity import views

app_name = 'activity'

urlpatterns = [
    path('<int:activity_id>/route', views.ThreeDView.as_view(), name='route'),
    path('<int:activity_id>/map.png', views.map_view, name='map'),
]
