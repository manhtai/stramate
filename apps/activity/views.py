from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

from apps.activity.models import Activity


@cache_control(public=True, max_age=315_360_000)
def map_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    file_path = activity.get_map_file()

    if file_path:
        return FileResponse(default_storage.open(file_path, 'rb'))

    return HttpResponse('')


class ThreeDView(TemplateView):
    template_name = "page/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        activity_id = kwargs.get('activity_id')
        activity = get_object_or_404(Activity, id=activity_id)
        context["activity"] = activity

        return context
