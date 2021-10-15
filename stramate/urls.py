from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='social')),

    path('account/', include('apps.account.urls')),
    path('activity/', include('apps.activity.urls')),
    path('', include('apps.page.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
