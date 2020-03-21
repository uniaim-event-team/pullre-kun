webapp_settings = {}
with open('app.ini', 'r') as f:
    for r in f.readlines():
        if r.find(' = ') > -1:
            key, value = r.split(' = ')
            webapp_settings[key] = value[:-1]
webapp_settings['mysql_connection'] = f'mysql+mysqlconnector://{webapp_settings["mysql_user"]}:' \
    f'{webapp_settings["mysql_pw"]}@{webapp_settings["mysql_host"]}:{webapp_settings["mysql_port"]}/' \
    f'{webapp_settings["mysql_db"]}?{webapp_settings["mysql_additional"]}'
