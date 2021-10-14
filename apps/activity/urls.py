from django.urls import path

from apps.activity import views

app_name = 'activity'

urlpatterns = [
    path('<int:activity_id>/3d', views.ThreeDView.as_view(), name='3d'),
    path('<int:activity_id>/map.png', views.map_view, name='map'),
]
