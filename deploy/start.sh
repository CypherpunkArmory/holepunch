#!/usr/bin/env bash

cd /holepunch
flask db upgrade
exec gunicorn --certfile=/secrets/cert.pem --keyfile=/secrets/key.pem -b :5000 --pythonpath /holepunch --access-logfile - --error-logfile - "app:create_app('production')"

