from collections import defaultdict
from datetime import datetime, timedelta
from os import path
from urllib.parse import quote_plus

import polyline
import pytz
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.urls import reverse_lazy
from django.utils.functional import cached_property

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


class Analytic(models.Model):
    date = models.DateField()
    timezone = models.TextField()

    heatmap = models.JSONField()
    fitness = models.JSONField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Analytics for {self.user} on {self.date}"

    class Meta:
        unique_together = (('date', 'user'),)


class Activity(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

    name = models.TextField(blank=True, db_index=True)
    type = models.TextField(blank=True)
    description = models.TextField(blank=True)

    distance = models.FloatField()  # m
    moving_time = models.PositiveIntegerField()  # s
    total_elevation_gain = models.FloatField()  # m
    average_speed = models.FloatField()  # m/s

    start_date = models.DateTimeField()
    timezone = models.TextField()
    start_date_local = models.DateTimeField()
    start_location = models.TextField(blank=True, db_index=True)  # place_name

    initial_rotation = models.IntegerField(default=-10)

    # Full data
    detail = models.JSONField()
    streams = models.JSONField()

    # Analytics
    analytics = models.JSONField()

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
            "analytics": dict(),
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
            lat, lon = self.coords[0]
            self.start_location = self._get_place_name(lat, lon)
            self.save()

        return self.start_location

    @property
    def map(self):
        return self.get_map_file()

    @property
    def coords(self):
        if self.polyline:
            return [[a, b] for (a, b) in polyline.decode(self.polyline)]
        return []

    @property
    def geojson_coords(self):
        if self.polyline:
            return [[b, a] for (a, b) in polyline.decode(self.polyline)]

        return []

    @property
    def calories(self):
        return f"{self.detail.get('calories', 0):,.0f} Cal"

    @property
    def average_hr(self):
        hr = self.detail.get('average_heartrate', 0)
        if hr:
            return f"{hr:.0f} bpm"
        return ""

    @property
    def max_hr(self):
        hr = self.detail.get('max_heartrate', 0)
        if hr:
            return f"{hr:.0f} bpm"
        return ''

    @classmethod
    def get_last_year_stats(cls, user_id):
        all_time_total = Activity.objects.filter(user_id=user_id).count()

        last_year = datetime.today() - timedelta(days=366)
        user_activities = Activity.objects.filter(
            user_id=user_id,
            start_date_local__gte=last_year,
        ).order_by('start_date')

        last = user_activities.last()
        timezone = last.timezone if last else "UTC"

        today = datetime.now().astimezone(pytz.timezone(timezone))

        last_year_activities = user_activities \
            .values('start_date_local') \
            .annotate(date=TruncDate('start_date_local')) \
            .values('date') \
            .annotate(
                moving=Sum('moving_time'),
                count=Count('id'),
            ) \
            .values('date', 'moving', 'count') \
            .order_by('date')

        last_year_dict = {
            d['date']: d['moving']
            for d in last_year_activities
        }

        last_year_total = sum(d['count'] for d in last_year_activities)

        last_year_moving = [
            {
                "x": d.strftime("%Y-%m-%d"),
                "y": (d + timedelta(days=1)).weekday(),
                "d": d.strftime("%b %-d, %Y"),
                "v": last_year_dict.get(d.date(), 0),
                "l": cls.format_time(last_year_dict.get(d.date(), 0)),
            }
            for i in range(0, 366)
            for d in [today - timedelta(days=i)]
        ]

        return {
            "all_time_total": all_time_total,
            "last_year_total": last_year_total,
            "last_year_moving": last_year_moving,
        }

    @cached_property
    def polyline(self):
        return self.detail.get("map") and self.detail["map"].get("polyline")

    @property
    def total_distance(self):
        if self.distance > 1_000:
            return f"{self.distance/1_000:.2f} km"
        return f"{self.distance} m"

    @property
    def total_elev(self):
        if self.total_elevation_gain > 1_000:
            return f"{self.total_elevation_gain/1_000:.2f} km"
        return f"{self.total_elevation_gain:.0f} m"

    @property
    def avg_pace(self):
        pace = 1_000 / self.average_speed
        [d, h, m, s] = self._get_units(pace)
        return f"{m}:{s:02} /km"

    @property
    def max_pace(self):
        pace = 1_000 / self.max_speed
        [d, h, m, s] = self._get_units(pace)
        return f"{m}:{s:02} /km"

    @property
    def avg_speed_mps(self):
        return f"{self.average_speed:.1f} m/s"

    @property
    def avg_speed_kph(self):
        return f"{self.average_speed * 3.6:.1f} km/h"

    @property
    def max_speed_mps(self):
        return f"{self.max_speed:.1f} m/s"

    @property
    def max_speed_kph(self):
        return f"{self.max_speed * 3.6:.1f} km/h"

    @cached_property
    def max_speed(self):
        return self.detail.get("max_speed", 0)

    @staticmethod
    def format_time(seconds):
        fdiff = ''
        [d, h, m, s] = Activity._get_units(seconds)

        if d > 0:
            fdiff += f'{d}d'

        if h > 0:
            fdiff += f' {h}h'

        if m > 0:
            fdiff += f' {m}m'

        if s > 0:
            fdiff += f' {s}s'

        return fdiff.strip()

    @property
    def total_moving_time(self):
        return self.format_time(self.moving_time)

    @property
    def heart_rate_zones(self):
        hr_zones = self.analytics.get("hr_zones")
        if not hr_zones:
            return []

        zones = defaultdict(int)
        for z in hr_zones:
            zones[z] += 1

        return [
            {
                "zone": i,
                "zonef": f"Zone {i}",
                "time": zones[i],
                "timef": self.format_time(zones[i]),
            }
            for i in [1, 2, 3, 4, 5]
        ]

    @property
    def stress_score(self):
        hrss = self.analytics.get("hrss")
        if hrss:
            return f"{hrss:.1f}"
        return "N/A"

    @staticmethod
    def _get_units(diff):
        d = int(diff / 86_400)
        h = int((diff - (d * 86_400)) / 3_600)
        m = int((diff - (d * 86_400 + h * 3_600)) / 60)
        s = int((diff - (d * 86_400 + h * 3_600 + m * 60)))
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

    def get_absolute_url(self):
        return reverse_lazy("activity:detail", args=(self.id,))

    def __str__(self):
        return f"{self.type} #{self.id}: {self.name}"

    class Meta:
        verbose_name_plural = "activities"
