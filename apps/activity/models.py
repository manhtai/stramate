from os import path
from urllib.parse import quote_plus

import polyline
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models

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

    start_date = models.DateTimeField()  # Timezone aware
    timezone = models.TextField()
    start_location = models.TextField()  # place, region

    # Full data
    detail = models.JSONField()
    streams = models.JSONField()

    # Relation
    athlete_id = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def upsert(cls, user_id, detail, streams):
        detail_dict = detail.to_dict()
        streams_dict = {k: v.to_dict() for k, v in streams.items()}

        defaults = {
            **{k: detail_dict.get(k) or v for k, v in FIELD_DEFAULTS.items()},
            "start_date": detail.start_date,
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
        file_path = path.join('map', f'activity-{self.id}.png')

        if not default_storage.exists(file_path):
            self._download_map(file_path)

        return file_path

    def get_start_location(self):
        if not self.start_location:
            coords = polyline.decode(self.detail["map"]["polyline"])
            lat, lon = coords[0]
            self.start_location = self._get_place_name(lat, lon)
            self.save()

        return self.start_location

    def _get_place_name(self, lat, lon):
        at = settings.MAPBOX_ACCESS_TOKEN
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json?types=place,region&access_token={at}"
        res = requests.get(url)
        geo = res.json()

        return geo['features'] and geo['features'][0] and geo['features'][0]['place_name'] or "Unknown"

    def _download_map(self, file_path):
        at = settings.MAPBOX_ACCESS_TOKEN
        pl = quote_plus(self.detail["map"]["polyline"])
        url = f"https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/static/path-3+ff0000-1({pl})/auto/1000x400?access_token={at}"

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
