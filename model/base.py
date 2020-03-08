from sqlalchemy import (
    orm,
    schema,
)
from sqlalchemy.ext.declarative import declarative_base


Session = orm.scoped_session(orm.sessionmaker())
metadata = schema.MetaData()
BaseObject = declarative_base(metadata=metadata)
