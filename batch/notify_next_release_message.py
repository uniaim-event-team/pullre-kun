import urllib.request
import re
import json

from config import webapp_settings
from mysql_dbcon import Connection
from model import NextReleaseMessage


if __name__ == '__main__':
    if not webapp_settings.get('slack_url') or\
        not webapp_settings.get('github_pr_column') or not webapp_settings.get('github_pr_suffix'):
        exit

    req = urllib.request.Request(webapp_settings['sha_url'])
    with urllib.request.urlopen(req) as res:
        sha = re.sub(r' .+', '', res.read().decode().replace('commit ', ''))
    if not sha:
        exit

    with Connection() as cn:
        next_release_message = cn.s.query(NextReleaseMessage).filter(
            NextReleaseMessage.sha == sha, NextReleaseMessage.state == 1).first()
        if not next_release_message or not next_release_message.content:
            exit

        next_release_notify_title = webapp_settings.get('next_release_notify_title', 'リリース待ちのバグリスクです！')
        column = webapp_settings.get('github_pr_column').replace(',', '|')
        suffix = webapp_settings.get('github_pr_suffix')
        message = '\n'.join(['\n'.join(map(str, v)) for v in re.findall(fr'({column})(.*?){suffix}', next_release_message.content)])\
            .replace('\\r\\n', '\n').replace('\\n\\r', '\n')
        req = urllib.request.Request(
            webapp_settings.get('slack_url'),
            data=json.dumps({'text': f'{next_release_notify_title}\n\n{message}'}).encode('utf-8'),
            method='POST', headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            print(res.read())