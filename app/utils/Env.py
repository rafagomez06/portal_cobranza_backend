import os
from dotenv import load_dotenv


class Env:
    """
    Centraliza la lectura de variables de entorno.
    Todas las variables usan el prefijo COBRANZA_ para evitar colisiones.
    """

    def __init__(self):
        load_dotenv()
        self.prefix = "COBRANZA_"

        # Flask
        self.flask_env   = os.getenv(f"{self.prefix}FLASK_ENV", "development")
        self.flask_debug = os.getenv(f"{self.prefix}FLASK_DEBUG", "1")

        # Base de datos
        self.db_host   = os.getenv(f"{self.prefix}DATABASE_HOST", "localhost")
        self.db_user   = os.getenv(f"{self.prefix}DATABASE_USER")
        self.db_passwd = os.getenv(f"{self.prefix}DATABASE_PASS")
        self.db_name   = os.getenv(f"{self.prefix}DATABASE_DB")
        self.db_port   = os.getenv(f"{self.prefix}DATABASE_PORT", "5432")

        # Seguridad
        self.secret_key     = os.getenv(f"{self.prefix}SECRET_KEY", "dev-secret")
        self.jwt_secret_key = os.getenv(f"{self.prefix}JWT_SECRET_KEY", "dev-jwt-secret")

        # Archivos
        self.upload_folder       = os.getenv(f"{self.prefix}UPLOAD_FOLDER", "uploads")
        self.max_content_length  = int(os.getenv(f"{self.prefix}MAX_CONTENT_LENGTH", 5242880))

        # Logs
        self.route_log = os.getenv(f"{self.prefix}LOG_FILE_ROUTE", "logs/")

class EnvSingleton:
    """
    Patrón Singleton: garantiza una sola instancia de Env en toda la app.
    Reutilizado de api_ecd_catalogos/src/utils/Env.py
    """
    _instance = None
    env_singleton = Env()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
