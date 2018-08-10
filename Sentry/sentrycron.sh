#!/bin/bash

source /home/someuser/.virtualenvs/sentry/bin/activate
cd /home/someuser/projects/onpremise
SENTRY_CONF=/home/someuser/.sentry sentry run cron