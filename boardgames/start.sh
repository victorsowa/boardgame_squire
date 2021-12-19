#!/usr/bin/env bash
gunicorn --bind 0.0.0.0:3031 wsgi:app
