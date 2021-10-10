from django.db import models
from django.contrib.auth.models import User


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

    def __str__(self):
        return f"{self.type} #{self.id}: {self.name}"

    class Meta:
        verbose_name_plural = "activities"
