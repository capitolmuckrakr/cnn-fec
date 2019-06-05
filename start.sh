#!/bin/bash

django-admin collectstatic --no-input
django-admin migrate

gunicorn config.prd.app \
    --bind 0.0.0.0:$PORT \
    --workers 2
