#!/bin/sh
# Run once

# curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -
# sudo apt-get install -y nodejs
# curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
# poetry install
# poetry run python manage.py tailwind install

git pull
poetry install

poetry run python manage.py tailwind build
poetry run python manage.py collectstatic --no-input
poetry run python manage.py migrate

pkill honcho
nohup poetry run honcho -f Procfile.prod start > honcho.log &
