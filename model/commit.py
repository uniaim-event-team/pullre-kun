from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Text,
    String,
    Integer,
)
from sqlalchemy.sql.functions import current_timestamp

from model.base import BaseObject


class Commit(BaseObject):
    __tablename__ = 'commits'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    sha = Column(String(40), unique=True, nullable=False)
    message = Column(Text)
    parent_a = Column(String(40))
    parent_b = Column(String(40))
    production_reported = Column(Integer)


class Issue(BaseObject):
    __tablename__ = 'issues'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=current_timestamp(), onupdate=current_timestamp(), nullable=False)
    number = Column(Integer, unique=True, nullable=False)
    state = Column(String(10))
    title = Column(Text)
    body = Column(Text)
    labels = Column(String(128))
    assignee = Column(String(128))
