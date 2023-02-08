import hashlib

from config import webapp_settings
from mysql_dbcon import Connection
from model import NextReleaseMessage
from service.pull_request import get_unreleased_pull_request


if __name__ == '__main__':
    with Connection() as cn:
        pull_requests = get_unreleased_pull_request()
        if not pull_requests:
            exit

        hash = hashlib.sha512(''.join(map(str, [pr.number for pr in pull_requests])).encode('utf-8')).hexdigest()[0:64]
        next_release_message = cn.s.query(NextReleaseMessage).filter(NextReleaseMessage.hash == hash).first()
        if next_release_message:
            exit

        if not next_release_message:
            cn.s.add(NextReleaseMessage(hash=hash, content='\n'.join([pr.body for pr in pull_requests])))
            cn.s.commit()

        cn.s.query(NextReleaseMessage).filter(NextReleaseMessage.hash != hash).delete(synchronize_session=False)
        cn.s.commit()
