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
        この関数の中身は _explicit_enterに移動しました。
        :return:
        """
        return self._explicit_enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        この関数の中身は_explicit_exitに移動しました。
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self._explicit_exit(exc_type, exc_val, exc_tb)

    def _explicit_enter(self, engine=None):
        """
        __enter__の中で行なっている処理(セッションの作成等)をここに移動して
        デバッグ時などに明示的にその処理を呼び出せるようにするための関数。
        基本は呼び出しちゃダメです。なのでプライベートメソッドにしてます。

        :return: self
        """
        self.engine = engine or c.engine
        Session.configure(bind=self.engine)
        self.s = Session()
        if self.execution_options:
            self.s.connection(execution_options=self.execution_options)
        return self

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def _explicit_exit(self, exc_type=None, exc_val=None, exc_tb=None):
        """
        __exit__の中で行なっている処理(セッションの破棄)をここに移動して
        デバッグ時などに明示的にその処理を呼び出せるようにするための関数。
        基本は呼び出しちゃダメです。なのでプライベートメソッドにしてます。
        """
        Session.remove()
