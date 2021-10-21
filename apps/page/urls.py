from django.urls import path

from apps.page.views import IndexView, ProfileView, RssView

app_name = 'page'

urlpatterns = [
    path('<username>/rss.xml', RssView(), name='rss'),
    path('<username>', ProfileView.as_view(), name='profile'),
    path('', IndexView.as_view(), name='index'),
]
