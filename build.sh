#!/usr/bin/env bash
set -e

python -m pip install --upgrade pip
pip install -r requirements/requirements.txt
python manage.py collectstatic --noinput
