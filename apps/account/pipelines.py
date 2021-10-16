from apps.activity.tasks import back_fill
from apps.account.models import Athlete


def initialize_activities_import(uid, is_new, user, *args, **kwargs):
    """
    Init import process the first time user created
    """
    if is_new:
        back_fill(uid)

    Athlete.get_athlete(user, uid=uid)
