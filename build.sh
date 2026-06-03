#!/usr/bin/env bash
set -e

python -m pip install --upgrade pip
pip install -r requirements/requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py create_default_users \
  --admin-username admintester \
  --admin-email admin@example.com \
  --admin-password "${DEFAULT_ADMIN_PASSWORD:-ChangeMeStrongly}" \
  --verifier-username verifier1 \
  --verifier-email verifier1@example.com \
  --verifier-password "${DEFAULT_VERIFIER_PASSWORD:-ChangeMeStrongly}" \
  --force
python manage.py shell << EOF
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Group

# Create second verifier account
user2, created = User.objects.get_or_create(username='verifier2')
user2.email = 'verifier2@example.com'
user2.is_active = True
user2.set_password('${DEFAULT_VERIFIER_PASSWORD:-ChangeMeStrongly}')
user2.save()

verifier_group = Group.objects.get(name='verifier')
user2.groups.add(verifier_group)

if created:
    print('Created verifier2 account')
else:
    print('Updated verifier2 account')
EOF
