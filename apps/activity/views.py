from django.http import FileResponse
from django.core.files.storage import default_storage
from apps.activity.models import Activity


def map_view(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    file_path = activity.get_map_file()
    return FileResponse(default_storage.open(file_path, 'rb'))
