#!/usr/bin/env bash

export PYTHONPATH=/home/ec2-user/pullre-kun
cd /home/ec2-user/pullre-kun/alembic
alembic revision --autogenerate -m update
alembic upgrade head
