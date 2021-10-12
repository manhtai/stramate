from django.http import FileResponse, HttpResponse
from django.views.decorators.cache import cache_control
from django.core.files.storage import default_storage
from apps.activity.models import Activity


@cache_control(public=True, max_age=315_360_000)
def map_view(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    file_path = activity.get_map_file()

    if file_path:
        return FileResponse(default_storage.open(file_path, 'rb'))

    return HttpResponse('')
