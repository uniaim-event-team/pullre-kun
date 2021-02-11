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
