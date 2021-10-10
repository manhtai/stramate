from apps.activity.tasks import initial_import


def initialize_activities_import(uid, is_new, *args, **kwargs):
    """
    Init import process the first time user created
    """
    if is_new:
        initial_import(uid)
