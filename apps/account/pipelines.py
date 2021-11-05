from apps.activity.tasks import back_fill
from apps.account.models import Athlete
from django.conf import settings


def initialize_activities_import(uid, is_new, user, *args, **kwargs):
    """
    Init import process the first time user created
    """
    Athlete.get_athlete(user, uid=uid)

    if is_new:
        if settings.DISABLE_REGISTRATION and Athlete.objects.count() > 1:
            user.is_active = False
            user.save()
        else:
            back_fill(uid)
