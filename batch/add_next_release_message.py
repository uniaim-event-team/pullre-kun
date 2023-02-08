import datetime
import re
import urllib.request

from config import webapp_settings
from mysql_dbcon import Connection
from model import NextReleaseMessage
from service.pull_request import get_unreleased_pull_request


if __name__ == '__main__':
    req = urllib.request.Request(webapp_settings['sha_url'])
    with urllib.request.urlopen(req) as res:
        sha = re.sub(r' .+', '', res.read().decode().replace('commit ', ''))
    if not sha:
        exit

    with Connection() as cn:
        next_release_message = cn.s.query(NextReleaseMessage).filter(NextReleaseMessage.sha == sha).first()
        if next_release_message is not None and (
            next_release_message.state == 1 or
            next_release_message.created_at > datetime.datetime.now() + datetime.timedelta(minutes=-1)
        ):
            exit

        pull_request = get_unreleased_pull_request()
        if not pull_request:
            exit

        if not next_release_message:
            next_release_message = NextReleaseMessage(state=2, sha=sha)
            cn.s.add(next_release_message)
            cn.s.commit()

        cn.s.query(NextReleaseMessage).filter(NextReleaseMessage.sha == sha) \
            .update({'state': 1, 'content': pull_request.body}, synchronize_session=False)
        cn.s.commit()

        cn.s.query(NextReleaseMessage).filter(NextReleaseMessage.sha != sha).delete(synchronize_session=False)
        cn.s.commit()
