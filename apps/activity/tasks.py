from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task, lock_task
from social_django.models import UserSocialAuth
from stravalib.client import Client
from django.conf import settings
from datetime import timedelta
from apps.activity.models import Activity
import polyline
import geocoder
import traceback


PROCESS_TIME = timedelta(minutes=5)
PULL_LIMIT = 200
STREAM_TYPES = ['time', 'latlng', 'distance', 'altitude', 'velocity_smooth',
                'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']


def update_start_location(activity, line):
    coords = polyline.decode(line)
    g = geocoder.mapbox(coords[0], method='reverse', key=settings.MAPBOX_ACCESS_TOKEN)
    start_location = f"{g.json['raw']['place']}, {g.json['raw']['region']}"
    activity.start_location = start_location
    activity.save()


def import_activities(athlete_id):
    client = Client()
    auth_user = UserSocialAuth.objects.get_social_auth("strava", athlete_id)

    client.access_token = auth_user.extra_data['access_token']
    if auth_user.expiration_timedelta() < PROCESS_TIME:
        res = client.refresh_access_token(
            client_id=settings.SOCIAL_AUTH_STRAVA_KEY,
            client_secret=settings.SOCIAL_AUTH_STRAVA_SECRET,
            refresh_token=auth_user.extra_data['refresh_token'],
        )
        auth_user.extra_data['access_token'] = res['access_token']
        auth_user.extra_data['expires'] = res['expires_at']
        auth_user.save()

    last_activity = Activity.objects.order_by('start_date').last()
    last_import_time = last_activity and last_activity.start_date

    for summary in client.get_activities(after=last_import_time, limit=PULL_LIMIT):
        try:
            detail = client.get_activity(summary.id, include_all_efforts=True)
            streams = client.get_activity_streams(summary.id, types=STREAM_TYPES)
            activity = Activity.upsert(auth_user.user_id, detail, streams)
            print("Update Strava data for:", activity)

            update_start_location(activity, detail.map.polyline)
            print("Update start location for:", activity)
        except Exception:
            traceback.print_exc()


@db_task()
def initial_import(athlete_id):
    with lock_task(f"import-{athlete_id}"):
        import_activities(athlete_id)


# TODO: Use webhook for this
@db_periodic_task(crontab(minute='*/5'))
def check_for_new_activities():
    for ua in UserSocialAuth.objects.filter(provider='strava'):
        with lock_task(f"import-{ua.uid}"):
            import_activities(ua.uid)
