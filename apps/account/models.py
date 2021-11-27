from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse_lazy


class Athlete(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    sex = models.TextField(blank=True)
    birthday = models.DateField()
    resting_hr = models.IntegerField(default=60)  # This may vary overtime, but may not effect that much

    hide_fitness = models.BooleanField(default=False)

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
        return reverse_lazy("page:profile", args=(self.user.username,))

    def __str__(self):
        return f"Athlete #{self.id}: #{self.user.username}"
