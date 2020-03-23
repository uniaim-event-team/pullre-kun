from typing import Optional

from sqlalchemy.engine import create_engine
from config import webapp_settings
from model import Session


class ConnectionPooling(object):
    def __init__(self, **params):
        self.engine = create_engine(webapp_settings['mysql_connection'], **params)


c = ConnectionPooling(max_overflow=50, pool_size=20, pool_recycle=3600, **webapp_settings.get('mysql_extra_param', {}))


class Connection:

    execution_options = None

    def __init__(self, execution_options=None):
        self.execution_options = execution_options
        self.s: Optional[Session] = None

    def __enter__(self):
        """
        create connection object
        :return:
        """
        self.engine = c.engine
        Session.configure(bind=self.engine)
        self.s = Session()
        if self.execution_options:
            self.s.connection(execution_options=self.execution_options)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        remove session
        """
        Session.remove()

    def upsert_from_form(self, model_class, form):
        args_dict = {}
        for column in model_class.__table__.columns:
            if hasattr(form, column.name) and getattr(form, column.name).data:
                # TODO Noneや''の時に更新されない
                args_dict[column.name] = getattr(form, column.name).data
        if form.id.data:
            # update (if form has id)
            id_ = form.id.data
            self.s.query(model_class).filter(model_class.id == id_).update(
                args_dict, synchronize_session=False)
        else:
            # create
            new_model = model_class(**args_dict)
            self.s.add(new_model)
            self.s.flush()
            self.s.refresh(new_model)
            id_ = new_model.id
        self.s.commit()
        return id_
