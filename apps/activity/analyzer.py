from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from apps.account.models import Athlete
from apps.activity.models import Activity


class PointAnalyzer():

    def __init__(self, activity_id: int):
        self.activity = Activity.objects.get(id=activity_id)
        self.athlete = Athlete.objects.get(id=self.activity.athlete_id)

    def analyze(self):
        self.init_metrics()

        # We only do heart rate base analytics for now
        if self.activity.detail.get('has_heartrate'):
            self.init_df()
            self.calculate_heartrate_stress_score()
            self.calculate_heartrate_zones()

            return {
                "min_hr": self.min_hr,
                "max_hr": self.max_hr,
                "hrss": self.hrss,

                "timestamp": [ts.timestamp() for ts in self.df.index.to_list()],
                "hr_zones": self.df['hr_zones'].to_list(),
                "heartrate": self.df['heartrate'].to_list(),
            }

        # Estimated max & manual input min
        return {
            "min_hr": self.min_hr,
            "max_hr": self.max_hr,
        }

    def init_metrics(self):
        self.trimp_factor = 1.92 if self.athlete.sex.upper() == 'M' else 1.67

        age = relativedelta(datetime.today(), self.athlete.birthday).years
        self.max_hr = 220 - age
        self.min_hr = self.athlete.resting_hr

    def init_df(self):
        # Which streams will be analyzed
        types = ['time', 'heartrate']

        self.df = pd.DataFrame(columns=types)
        for type in types:
            self.df[type] = pd.Series(self.activity.streams[type]["data"], index=None)

        # Add timestamp col
        self.df['start_date'] = self.activity.start_date
        self.df['timestamp'] = pd.Series(map(
            lambda s, d: d + timedelta(seconds=int(s)),
            self.df['time'], self.df['start_date']))
        self.df.set_index('timestamp', inplace=True)

        # Resample
        self.df = self.df.resample('1S').mean()
        self.df = self.df.interpolate(limit_direction='both')

    def calculate_heartrate_stress_score(self):
        lthr = ((self.max_hr - self.min_hr) * 0.85) + self.min_hr  # Karvonen formula

        self.df['hrr'] = self.df['heartrate'].apply(
            lambda x: (x - self.min_hr) / (self.max_hr - self.min_hr)
        )

        trimp = (
            (1 / 60) * self.df['hrr'] * (0.64 * np.exp(self.trimp_factor * self.df['hrr']))
        ).sum()

        hrr_lthr = (lthr - self.min_hr) / (self.max_hr - self.min_hr)
        self.hrss = (
            trimp / (60 * hrr_lthr * (0.64 * np.exp(self.trimp_factor * hrr_lthr)))
        ) * 100

    def calculate_heartrate_zones(self):
        self.df["hr_zones"] = self.df['heartrate'].apply(
            lambda x: Activity.map_zone(x, self.max_hr, self.min_hr)
        )


class TrendAnalyzer():
    # Ref: https://www.trainingpeaks.com/coach-blog/a-coachs-guide-to-atl-ctl-tsb/
    atl_days = 7
    ctl_days = 42
    year_days = 365

    def __init__(self, athlete_id):
        self.athlete_id = athlete_id

    def analyze(self):
        last_year = datetime.today() - timedelta(days=self.year_days + self.ctl_days)
        user_activities = Activity.objects.filter(
            athlete_id=self.athlete_id,
            start_date_local__gte=last_year,
        ).order_by('start_date')

        last = user_activities.last()
        self.timezone = pytz.timezone(last and last.timezone or "UTC")
        self.user = last.user

        today = datetime.now().astimezone(self.timezone)
        last_year = today - timedelta(days=self.year_days + 1)

        user_analytics = user_activities.values("analytics", "start_date_local")

        if len(user_analytics):
            self.df = pd.DataFrame(user_analytics)

            today_local = today.replace(tzinfo=None).astimezone()
            self.df = self.df.append(
                {"start_date_local": today_local, "analytics": {}},
                ignore_index=True,
            )

            return self.calculate_fitness_performance()

        return {}

    def timestamp_date(self, ts: pd.Timestamp):
        return ts.to_pydatetime().replace(tzinfo=None).astimezone(self.timezone).strftime("%Y-%m-%d")

    @classmethod
    def get_last_year_stats(cls, user_id):
        all_time_total = Activity.objects.filter(user_id=user_id).count()
        distances = Activity.objects \
            .filter(user_id=user_id, type__in=["Ride", "Run", "Swim"]) \
            .values("type") \
            .annotate(
                distance=Sum('distance')
            ) \
            .values("type", "distance") \
            .order_by("type")

        all_time_distance = {
            d['type']: f"{d['distance'] / 1000:.1f}"
            for d in distances
        }

        last_year = datetime.today() - timedelta(days=cls.year_days + 1)
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
                "l": Activity.format_time(last_year_dict.get(d.date(), 0)),
            }
            for i in range(cls.year_days)
            for d in [today - timedelta(days=i)]
        ]

        return {
            "all_time_total": all_time_total,
            "all_time_distance": all_time_distance,
            "last_year_total": last_year_total,
            "last_year_moving": last_year_moving,
        }

    def calculate_fitness_performance(self):
        # Index by date to resample
        self.df['date'] = pd.to_datetime(self.df['start_date_local'], utc=True)
        self.df.set_index('date', inplace=True)

        self.df['hrss'] = self.df["analytics"].map(
            lambda a: a.get('hrss', 0) if type(a) is dict else 0
        ).fillna(0)
        self.df = self.df[['hrss']].resample('D').sum()

        # Calculate perf. using hrss for now
        self.df['ctl'] = self.df['hrss'].ewm(span=self.ctl_days).mean()
        self.df['atl'] = self.df['hrss'].ewm(span=self.atl_days).mean()
        self.df['tsb'] = self.df['ctl'] - self.df['atl']

        self.df.drop(columns='hrss', inplace=True)

        last_year = pd.Timestamp.utcnow() - pd.Timedelta(days=self.year_days)
        return [
            {**v, "x": self.timestamp_date(k)}
            for k, v in self.df.to_dict(orient="index").items()
            if k > last_year
        ]
