import re
import urllib.request

from sqlalchemy import and_

from config import webapp_settings
from model import PullRequest
from model.commit import Commit
from mysql_dbcon import Connection


def get_unreleased_pull_request():
    with Connection() as cn:
        return cn.s.query(PullRequest)\
            .join(Commit, and_(Commit.sha == PullRequest.sha, Commit.production_reported == 0))\
            .filter(PullRequest.state == 'closed')\
            .order_by(PullRequest.number)\
            .all()