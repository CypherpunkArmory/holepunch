#!/usr/bin/env bash

cd /holepunch
flask db upgrade
exec gunicorn -b :5000 --pythonpath /holepunch --access-logfile - --error-logfile - "app:create_app('production')"

