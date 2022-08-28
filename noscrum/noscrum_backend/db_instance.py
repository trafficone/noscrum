from flask_sqlalchemy import SQLAlchemy


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        if args != (None,):
            cls._instances[cls].init_app(args[0])
        return cls._instances[cls]


class DBSingleton(SQLAlchemy, metaclass=Singleton):
    pass


def get_db_instance(flask_app=None):
    global DB_SET
    if flask_app is not None:
        DB_SET = True
    return DBSingleton(flask_app)
