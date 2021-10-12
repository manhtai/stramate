#!/bin/sh
# Run once
# curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
# poetry install
# poetry run honcho -f Procfile.prod export -a stramate supervisord /etc/supervisor/conf.d
git pull
poetry run python manage.py collectstatic --no-input
poetry run python manage.py migrate
sudo supervisor restart stramate
