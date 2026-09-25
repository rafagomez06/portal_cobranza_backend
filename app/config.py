from app.utils.Env import EnvSingleton
from datetime import timedelta
import urllib # Importante para codificar la cadena ODBC

env = EnvSingleton().env_singleton


def _build_db_uri() -> str:
    """Construye la URI de conexión para SQL Server 2008 ."""

    odbc_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={env.db_host},{env.db_port};"
        f"DATABASE={env.db_name};"
        f"UID={env.db_user};"
        f"PWD={env.db_passwd};"
    )
    
    # Codificamos la cadena para que sea segura en una URL
    params = urllib.parse.quote_plus(odbc_str)
    
    # Retornamos el formato
    return f"mssql+pyodbc:///?odbc_connect={params}"

class Config:
    """Configuración base compartida por todos los entornos."""
    SECRET_KEY = env.secret_key
    JWT_SECRET_KEY = env.jwt_secret_key
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = env.upload_folder
    MAX_CONTENT_LENGTH = env.max_content_length

    # JWT token expira en 8 horas por defecto
    #JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    #JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=20)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _build_db_uri()
    SQLALCHEMY_ECHO = False # Imprime el SQL generado en consola


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _build_db_uri()
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"   # BD en memoria para tests
    SQLALCHEMY_ECHO = False


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}
