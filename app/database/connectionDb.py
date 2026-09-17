
from flask_sqlalchemy import SQLAlchemy

class ConnectionDb:
    _instance = None
    alchemy_db = SQLAlchemy()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance
