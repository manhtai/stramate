from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse_lazy


class Athlete(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Heart rate zones will be calculated base on these number
    birthday = models.DateField()
    hr_zone_threshold_1 = models.FloatField(default=.6)
    hr_zone_threshold_2 = models.FloatField(default=.7)
    hr_zone_threshold_3 = models.FloatField(default=.8)
    hr_zone_threshold_4 = models.FloatField(default=.9)

    @classmethod
    def get_athlete(cls, user, uid=None):
        if not uid:
            au = user.social_auth.first()
            uid = au.uid

        ath, _ = Athlete.objects.get_or_create(id=uid, defaults={
            'birthday': date.today() - relativedelta(years=30),
            'user_id': user.id,
        })

        return ath

    def get_absolute_url(self):
        return reverse_lazy("account:athlete")

    def __str__(self):
        return f"Athlete #{self.id}: #{self.user.username}"
