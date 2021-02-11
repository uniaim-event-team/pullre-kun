import os
import re
import shutil
import subprocess

import pytest

import mysql_dbcon
from app import create_app, webapp_settings

webapp_settings['protocol'] = 'http://'

# circle ciでは動かないかも
new_connection_string = webapp_settings['mysql_connection'].replace('pullre', 'test_pullre')
if new_connection_string == webapp_settings['mysql_connection']:
    raise (Exception('No pullre at db name'))
new_db = re.sub(r'\?.+', '', re.sub('.+/', '', new_connection_string))

with mysql_dbcon.Connection() as cn:
    try:
        cn.engine.execute('drop database ' + new_db)
    except Exception as e:
        print(e)

with mysql_dbcon.Connection() as cn:
    try:
        cn.engine.execute('create database ' + new_db + ' character set utf8mb4')
    except Exception as e:
        print(e)

try:
    # alembic
    try:
        shutil.rmtree("alembic_copy")
    except Exception as e:
        print(e)
    shutil.copytree("alembic", "alembic_copy")
    shutil.rmtree("alembic_copy/alembic/versions")
    os.mkdir("alembic_copy/alembic/versions")
    with open('alembic_copy/alembic.ini', 'r') as f:
        lines = f.readlines()
        for i in range(len(lines)):
            if lines[i].find('pullre') > -1:
                lines[i] = lines[i].replace('pullre', 'test_pullre')
    with open('alembic_copy/alembic.ini', 'w') as f:
        for line in lines:
            f.write(line + '\n')
    res = subprocess.check_output(
        'export PYTHONPATH=' + webapp_settings['base_dir'] + '/pullre-kun/; cd alembic_copy;'
        ' alembic revision --autogenerate -m "test"; alembic upgrade head', shell=True)
    shutil.rmtree("alembic_copy")

except Exception as e:
    raise e
webapp_settings['mysql_connection'] = new_connection_string
mysql_dbcon.c = mysql_dbcon.ConnectionPooling(max_overflow=50, pool_size=20)


@pytest.fixture
def app():
    app = create_app()
    app.debug = True
    if False:
        yield app
    return
    # return app
    # ctx = app.test_request_context()
    # ctx.push()
    #
    # yield app
    #
    # ctx.pop()
