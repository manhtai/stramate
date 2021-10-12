#!/bin/sh
# Run once

# curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -
# sudo apt-get install -y nodejs supervisor
# curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
# poetry install
# poetry run python manage.py tailwind init
# cp supervisor.conf /etc/supervisor/conf.d/


git pull

poetry run python manage.py tailwind build
poetry run python manage.py collectstatic --no-input
poetry run python manage.py migrate
sudo supervisor stramate restart
