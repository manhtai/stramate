from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from apps.account.models import Athlete
from apps.activity.models import Activity
import numpy as np
import pandas as pd


class SingleAnalyzer():

    def __init__(self, activity: Activity, athlete: Athlete):
        self.activity = activity
        self.athlete = athlete

        # We only do heart rate base analytics for now
        if self.activity.detail.get('has_heartrate'):
            self.init_metrics()
            self.init_df()
            self.perform_analytics()
            self.save_analytics()

    def perform_analytics(self):
        self.calculate_heartrate_stress_score()

    def save_analytics(self):
        self.activity.analytics = {
            "hrss": self.hrss
        }
        self.activity.save()

    def init_metrics(self):
        self.trimp_weighting_factor = 1.92 if self.athlete.gender.upper() == 'M' else 1.67

        age = relativedelta(datetime.today(), self.athlete.birthday).years
        self.hr_max = 220 - age
        self.hr_min = self.athlete.resting_hr

    def init_df(self):
        # Which streams will be analyzed
        types = ['time', 'heartrate']

        self.df = pd.DataFrame(columns=types)
        for type in types:
            self.df[type] = pd.Series(self.streams[type].data, index=None)

        # Add timestamp col
        self.df['start_date'] = self.activity.start_date
        self.df['timestamp'] = pd.Series(map(
            lambda s, d: d + timedelta(seconds=int(s)), self.df['time'], self.df['start_date']))
        self.df.set_index('timestamp', inplace=True)

        # Resample
        self.df = self.df.resample('1S').mean()
        self.df = self.df.interpolate(limit_direction='both')

    def calculate_heartrate_stress_score(self):
        athlete_lthr = ((self.hr_max - self.hr_min) * .85) + self.hr_min  # Karvonen

        self.df['hrr'] = self.df['heartrate'].apply(lambda x: (x - self.hr_min) / (self.hr_max - self.hr_min))

        self.trimp = ((1 / 60) * self.df['hrr'] * (
            0.64 * np.exp(self.trimp_weighting_factor * self.df['hrr']))).sum()

        athlete_hrr_lthr = (athlete_lthr - self.hr_min) / (self.hr_max - self.hr_min)
        self.hrss = (self.trimp / (
            60 * athlete_hrr_lthr * (0.64 * np.exp(self.trimp_weighting_factor * athlete_hrr_lthr)))) * 100


class ProgressAnalyzer():

    def __init__(self):
        self.df = pd.readsql()

    def calculate_performance(self):
        atl_days = 7
        ctl_days = 42

        self.df['stress_score'] = self.df['hrss']
        df = self.df[['stress_score']].resample('D').sum()

        df['ctl'] = df['tss'].rolling(ctl_days, min_periods=1).mean()
        df['atl'] = df['tss'].rolling(atl_days, min_periods=1).mean()
        df['tsb'] = df['ctl'].shift(1) - df['atl'].shift(1)
