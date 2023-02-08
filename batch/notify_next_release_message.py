import hashlib
import urllib.request
import re
import json

from config import webapp_settings
from mysql_dbcon import Connection
from model import NextReleaseMessage
from service.pull_request import get_unreleased_pull_request


if __name__ == '__main__':
    if not webapp_settings.get('slack_url') or\
        not webapp_settings.get('github_pr_column') or not webapp_settings.get('github_pr_suffix'):
        exit

    pull_requests = get_unreleased_pull_request()
    if not pull_requests:
        exit

    with Connection() as cn:
        hash = hashlib.sha512(''.join(map(str, [pr.number for pr in pull_requests])).encode('utf-8')).hexdigest()[0:64]
        next_release_message = cn.s.query(NextReleaseMessage).filter(NextReleaseMessage.hash == hash).first()
        if not next_release_message or not next_release_message.content:
            exit

        next_release_notify_title = webapp_settings.get('next_release_notify_title', 'リリース待ちのバグリスクです！')
        column = webapp_settings.get('github_pr_column').replace(',', '|')
        suffix = webapp_settings.get('github_pr_suffix')
        message = '\n'.join([v[1] for v in re.findall(fr'({column})((.|\s)*?){suffix}', next_release_message.content)])\
            .replace('\\r\\n', '\n').replace('\\n\\r', '\n').replace('\\n', '\n')
        req = urllib.request.Request(
            webapp_settings.get('slack_url'),
            data=json.dumps({'text': f'{next_release_notify_title}\n\n{message}'}).encode('utf-8'),
            method='POST', headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            print(res.read())