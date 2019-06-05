#!/bin/bash

django-admin collectstatic
django-admin migrate

gunicorn config.prd.application \
    --bind 0.0.0.0:$PORT \
    --workers 2
