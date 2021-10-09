from django.db import models


class Activity(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

    # Overview data
    name = models.TextField()
    type = models.TextField()
    description = models.TextField()
    distance = models.FloatField()  # m
    moving_time = models.PositiveIntegerField()  # s
    total_elevation_gain = models.FloatField()  # s
    average_speed = models.FloatField()  # m/s
    start_date = models.DateTimeField()

    start_lat = models.FloatField()
    start_lon = models.FloatField()
    start_location = models.JSONField()

    # Full data
    detail = models.JSONField()
    streams = models.JSONField()
