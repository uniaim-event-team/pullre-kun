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

    pull_requests = relationship('PullRequest', back_populates='server')


class PullRequest(BaseObject):
    __tablename__ = 'pull_requests'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    number = Column(Integer)
    state = Column(String(20))
    sha = Column(String(64))
    title = Column(Text)
    ref = Column(Text)
    server_id = Column(BigInteger, ForeignKey('servers.id'))

    server = relationship('Server', back_populates='pull_requests')
