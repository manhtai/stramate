import time
import traceback
from datetime import datetime, timedelta

from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from social_django.models import UserSocialAuth
from stravalib.client import Client

from apps.activity.models import Activity, Analytic

PROCESS_TIME = timedelta(minutes=5)
PULL_LIMIT = 200
STREAM_TYPES = ['time', 'latlng', 'distance', 'altitude', 'velocity_smooth',
                'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']


@db_task()
def update_trend_analytics(athlete_id):
    from apps.activity.analyzer import TrendAnalyzer
    ta = TrendAnalyzer(athlete_id)
    trend = ta.analyze()

    if trend and trend[-1]['x']:
        date = trend[-1]['x']

        heatmap = Activity.get_last_year_stats(ta.user.id)
        Analytic.objects.update_or_create(
            date=date, user=ta.user,
            defaults={"fitness": trend, "heatmap": heatmap, "timezone": ta.timezone.zone}
        )


@db_task()
def update_activity_analytics(activity_id):
    from apps.activity.analyzer import PointAnalyzer
    pa = PointAnalyzer(activity_id)

    pa.activity.analytics = pa.analyze()
    pa.activity.save()


def get_client(auth_user):
    client = Client()

    client.access_token = auth_user.extra_data['access_token']
    if auth_user.expiration_timedelta() < PROCESS_TIME:
        res = client.refresh_access_token(
            client_id=settings.SOCIAL_AUTH_STRAVA_KEY,
            client_secret=settings.SOCIAL_AUTH_STRAVA_SECRET,
            refresh_token=auth_user.extra_data['refresh_token'],
        )

        epoch_now = int(datetime.utcnow().timestamp())
        auth_user.extra_data['access_token'] = res['access_token']
        auth_user.extra_data['expires'] = res['expires_at'] - epoch_now
        auth_user.extra_data['auth_time'] = epoch_now
        auth_user.save()

    return client


def import_activity(client, auth_user, activity_id):
    try:
        detail = client.get_activity(activity_id, include_all_efforts=True)
        streams = client.get_activity_streams(activity_id, types=STREAM_TYPES)
        activity = Activity.upsert(auth_user.user_id, detail, streams)
        print("Created Strava activity:", activity)

        update_activity_analytics(activity.id)
        activity.get_start_location()
        activity.get_map_file()
    except Exception:
        traceback.print_exc()


def import_activities(athlete_id):
    auth_user = UserSocialAuth.objects.get_social_auth("strava", athlete_id)
    client = get_client(auth_user)

    last_activity = Activity.objects.order_by('start_date').last()
    last_import_time = last_activity and last_activity.start_date
    activities = client.get_activities(after=last_import_time, limit=PULL_LIMIT)

    count = 0
    for summary in activities:
        import_activity(client, auth_user, summary.id)
        count += 1

    return count


@db_task()
def back_fill(athlete_id):
    auth_user = UserSocialAuth.objects.get_social_auth("strava", athlete_id)
    client = get_client(auth_user)

    last_import_time = datetime.utcnow()
    done = False

    count = 0
    while not done:
        activities = client.get_activities(before=last_import_time, limit=PULL_LIMIT)
        count += 1

        active = False
        for summary in activities:
            active = True
            last_import_time = summary.start_date

            if Activity.objects.filter(id=summary.id).exists():
                print(f"Skip activity: #{summary.id}")
                continue

            print(f"Import activty: #{summary.id}")
            import_activity(client, auth_user, summary.id)
            count += 2

        done = not active

        # Avoid rate limit
        if count > 400:
            time.sleep(60)
            count = 0


# TODO: Use webhook for this
@db_periodic_task(crontab(minute='*/5'))
def check_for_new_activities():
    for ua in UserSocialAuth.objects.filter(provider='strava'):
        imported = import_activities(ua.uid)
        if imported:
            update_trend_analytics(ua.uid)
