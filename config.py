webapp_settings = {}
with open('app.ini', 'r') as f:
    for r in f.readlines():
        if r.find(' = ') > -1:
            key, value = r.split(' = ')
            webapp_settings[key] = value[:-1]
