import subprocess

from config import webapp_settings


if __name__ == '__main__':
    with open('alembic/alembic.ini.default', 'r') as f:
        lines = f.readlines()
    with open('alembic/alembic.ini', 'w') as f:
        f.write(''.join(lines).replace('[mysql_connection]', webapp_settings['mysql_connection']))
    try:
        subprocess.check_output('sh ./init_db.sh', shell=True)
    except Exception as ex:
        print(ex.__dict__)
        raise ex
