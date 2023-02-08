from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Text,
    String,
    Integer,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import current_timestamp

from model.base import BaseObject


class Server(BaseObject):
    __tablename__ = 'servers'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    instance_id = Column(String(100))
    name = Column(Text)
    private_ip = Column(String(100))
    db_schema = Column(Text)
    check_url = Column(Text)
    is_staging = Column(Integer, default=0)
    auto_start_at = Column(DateTime)
    auto_stop_at = Column(DateTime)

    pull_requests = relationship('PullRequest', back_populates='server')


class HideServer(BaseObject):
    __tablename__ = 'hide_servers'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    name = Column(Text)


class PullRequest(BaseObject):
    __tablename__ = 'pull_requests'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    number = Column(Integer, nullable=False, unique=True)
    state = Column(String(20))
    sha = Column(String(64))
    title = Column(Text)
    body = Column(Text)
    ref = Column(Text)
    server_id = Column(BigInteger, ForeignKey('servers.id'))
    is_launched = Column(Integer)
    db_schema = Column(Text)
    check_run_id = Column(BigInteger)

    server = relationship('Server', back_populates='pull_requests')


class GitHubUser(BaseObject):
    __tablename__ = 'git_hub_users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    login = Column(String(128), nullable=False, unique=True)
    db_schema = Column(Text)


class NextReleaseMessage(BaseObject):
    __tablename__ = 'next_release_messages'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    # 1: done, 2: inprogress
    state = Column(Integer)
    sha = Column(String(40), unique=True, nullable=False)
    content = Column(Text)
