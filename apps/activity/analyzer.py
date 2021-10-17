from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta

from apps.account.models import Athlete
from apps.activity.models import Activity


class PointAnalyzer():

    HEART_RATE_ZONES = [.6, .7, .8, .9]

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

        self.df['hrr'] = self.df['heartrate'].apply(lambda x: (x - self.min_hr) / (self.max_hr - self.min_hr))

        self.trimp = ((1 / 60) * self.df['hrr'] * (
            0.64 * np.exp(self.trimp_factor * self.df['hrr']))).sum()

        hrr_lthr = (lthr - self.min_hr) / (self.max_hr - self.min_hr)
        self.hrss = (self.trimp / (60 * hrr_lthr * (0.64 * np.exp(self.trimp_factor * hrr_lthr)))) * 100

    def calculate_heartrate_zones(self):
        hrr = self.max_hr - self.min_hr

        z1 = round((hrr * self.HEART_RATE_ZONES[0]) + self.min_hr)
        z2 = round((hrr * self.HEART_RATE_ZONES[1]) + self.min_hr)
        z3 = round((hrr * self.HEART_RATE_ZONES[2]) + self.min_hr)
        z4 = round((hrr * self.HEART_RATE_ZONES[3]) + self.min_hr)

        self.df["hr_zones"] = self.df['heartrate'].apply(lambda x: self.map_zone(x, z1, z2, z3, z4))

    @staticmethod
    def map_zone(heartrate, z1, z2, z3, z4):
        if not heartrate:
            return 0
        if heartrate <= z1:
            return 1
        if heartrate <= z2:
            return 2
        if heartrate <= z3:
            return 3
        if heartrate <= z4:
            return 4
        return 5


class TrendAnalyzer():

    def __init__(self, athlete_id):
        self.athlete_id = athlete_id

    def analyze(self):
        last_year = datetime.today() - timedelta(days=366)
        user_activities = Activity.objects.filter(
            athlete_id=self.athlete_id,
            start_date_local__gte=last_year,
        ).order_by('start_date')

        last = user_activities.last()
        self.timezone = pytz.timezone(last and last.timezone or "UTC")
        self.user = last.user

        today = datetime.now().astimezone(self.timezone)
        last_year = today - timedelta(days=366)

        user_analytics = user_activities.values("analytics", "start_date_local")

        if len(user_analytics):
            self.df = pd.DataFrame(user_analytics)

            today_local = today.replace(tzinfo=None).astimezone()
            self.df = self.df.append({"start_date_local": today_local, "analytics": {}}, ignore_index=True)

            return self.calculate_fitness_performance()

        return {}

    def timestamp_date(self, ts: pd.Timestamp):
        return ts.to_pydatetime().replace(tzinfo=None).astimezone(self.timezone).strftime("%Y-%m-%d")

    def calculate_fitness_performance(self):
        # Ref: https://www.trainingpeaks.com/coach-blog/a-coachs-guide-to-atl-ctl-tsb/
        atl_days = 7
        ctl_days = 42

        # Index by date to resample
        self.df['date'] = pd.to_datetime(self.df['start_date_local'], utc=True)
        self.df.set_index('date', inplace=True)

        self.df['hrss'] = self.df["analytics"].map(lambda a: a.get('hrss', 0) if type(a) is dict else 0).fillna(0)
        self.df = self.df[['hrss']].resample('D').sum()

        # Calculate perf. using hrss for now
        self.df['ctl'] = self.df['hrss'].rolling(ctl_days, min_periods=1).mean()
        self.df['atl'] = self.df['hrss'].rolling(atl_days, min_periods=1).mean()
        self.df['tsb'] = self.df['ctl'] - self.df['atl']

        self.df.drop(columns='hrss', inplace=True)

        return [
            {**v, "x": self.timestamp_date(k)}
            for k, v in self.df.to_dict(orient="index").items()
        ]
