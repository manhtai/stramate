from datetime import datetime, timedelta
from os import path
from urllib.parse import quote_plus

import polyline
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Count
from django.db.models.functions import TruncDate


FIELD_DEFAULTS = {
    "id": 0,
    "name": "",
    "type": "",
    "description": "",
    "distance": 0,
    "moving_time": 0,
    "total_elevation_gain": 0,
    "average_speed": 0,
    "timezone": "UTC",
}


class Activity(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

    name = models.TextField(blank=True)
    type = models.TextField(blank=True)
    description = models.TextField(blank=True)

    distance = models.FloatField()  # m
    moving_time = models.PositiveIntegerField()  # s
    total_elevation_gain = models.FloatField()  # s
    average_speed = models.FloatField()  # m/s

    start_date = models.DateTimeField()
    timezone = models.TextField()
    start_date_local = models.DateTimeField()
    start_location = models.TextField()  # place_name

    # Full data
    detail = models.JSONField()
    streams = models.JSONField()

    # Relation
    athlete_id = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def upsert(cls, user_id, detail, streams):
        detail_dict = detail.to_dict()
        streams_dict = {k: v.to_dict() for k, v in streams.items()} if streams else {}

        defaults = {
            **{k: detail_dict.get(k) or v for k, v in FIELD_DEFAULTS.items()},
            "start_date": detail.start_date,
            "start_date_local": detail.start_date_local,
            "athlete_id": detail.athlete.id,
            "user_id": user_id,
            "detail": detail_dict,
            "streams": streams_dict,
        }

        act, _ = Activity.objects.update_or_create(
            **defaults,
            defaults=defaults,
        )
        return act

    def get_map_file(self):
        if self.start_location:
            file_path = path.join('map', f'activity-{self.id}.png')

            if not default_storage.exists(file_path):
                self._download_map(file_path)

            return file_path

        return ""

    def get_start_location(self):
        if not self.start_location and self.polyline:
            coords = polyline.decode(self.polyline)
            lat, lon = coords[0]
            self.start_location = self._get_place_name(lat, lon)
            self.save()

        return self.start_location

    @classmethod
    def get_last_year_stats(cls, user_id):
        activities = Activity.objects.filter(user_id=user_id)
        recent_limit = 3

        last_year = datetime.today() - timedelta(days=365)
        last_month = datetime.today() - timedelta(days=30)

        all_time_total = activities.count()
        last_month_total = activities.filter(start_date_local__gte=last_month).count()

        recent_activities = activities.order_by('-start_date')[:recent_limit]
        last_year_activities = activities \
            .filter(start_date_local__gte=last_year) \
            .annotate(date=TruncDate('start_date_local')) \
            .values('date') \
            .annotate(count=Count('id')) \
            .values('date', 'count')

        last_year_dict = {
            d['date']: d['count']
            for d in last_year_activities
        }

        last_year_total = sum(d['count'] for d in last_year_activities)

        last_year_count = [
            {
                "x": d.strftime("%Y-%m-%d"),
                "y": str(d.isoweekday()),
                "d": d.strftime("%b %-d, %Y"),
                "v": last_year_dict.get(d.date(), 0),
            }
            for i in range(1, 366)
            for d in [last_year + timedelta(days=i)]
        ]

        return {
            "all_time_total": all_time_total,
            "last_month_total": last_month_total,
            "recent_activities": recent_activities,
            "last_year_total": last_year_total,
            "last_year_count": last_year_count,
        }

    @property
    def polyline(self):
        return self.detail.get("map") and self.detail["map"].get("polyline")

    @property
    def format_distance(self):
        if self.distance > 1_000:
            return f"{self.distance/1_000:.2f} km"
        return f"{self.distance} m"

    @property
    def format_elev(self):
        if self.total_elevation_gain > 1_000:
            return f"{self.total_elevation_gain/1_000:.2f} km"
        return f"{self.total_elevation_gain:.0f} m"

    @property
    def format_pace(self):
        pace = 1_000 / self.average_speed
        [d, h, m, s] = self._get_units(pace)
        return f"{m}:{s:02} /km"

    @property
    def format_speed(self):
        return f"{self.average_speed:.1f} m/s"

    @property
    def format_moving_time(self):
        [d, h, m, s] = self._get_units(self.moving_time)
        if d > 0:
            fdiff = f'{d}d {h}h {m}m'
        elif h > 0:
            fdiff = f'{h}h {m}m'
        elif m > 0:
            fdiff = f'{m}m {s}s'
        else:
            fdiff = f'{s}s'
        return fdiff

    def _get_units(self, diff):
        d = int(diff / 86400)
        h = int((diff - (d * 86400)) / 3600)
        m = int((diff - (d * 86400 + h * 3600)) / 60)
        s = int((diff - (d * 86400 + h * 3600 + m * 60)))
        return [d, h, m, s]

    def _get_place_name(self, lat, lon):
        at = settings.MAPBOX_ACCESS_TOKEN
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json?types=place,region&access_token={at}"
        res = requests.get(url)
        geo = res.json()

        return geo['features'] and geo['features'][0] and geo['features'][0]['place_name'] or "Unknown"

    def _download_map(self, file_path):
        at = settings.MAPBOX_ACCESS_TOKEN
        pl = quote_plus(self.detail["map"]["polyline"])
        url = f"https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/static/path-3+ff0000-1({pl})/auto/1000x400@2x?padding=50&access_token={at}"

        with requests.get(url, stream=True) as r:
            r.raise_for_status()

            default_storage.save(file_path, ContentFile(b''))  # Trick to create file

            with default_storage.open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return path

    def __str__(self):
        return f"{self.type} #{self.id}: {self.name}"

    class Meta:
        verbose_name_plural = "activities"
