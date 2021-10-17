# StraMate

> A self-hosted data analyzer for your Strava activities

## Notice

You should host it yourself, don't give your data to arbitrary people on the internet!

## Local setup

```sh
poetry install
poetry run python manage.py migrate
poetry run honcho start
```

## Features

- [x] Activities heat map
- [x] Fitness & fatigue performance chart
- [x] Interactive 3D map

## Deployment

- [x] Use `sqlite` for database, no `postgres` or `mysql`
- [x] Use `sqlite` for queue broker, no `redis` or `rabbitmq`

See [deploy.sh](./deploy.sh) for instruction on Ubuntu.
