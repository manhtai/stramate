from apps.activity.tasks import back_fill


def initialize_activities_import(uid, is_new, *args, **kwargs):
    """
    Init import process the first time user created
    """
    if is_new:
        back_fill(uid)
