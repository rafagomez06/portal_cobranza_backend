import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import date

from app.utils.Env import EnvSingleton

env = EnvSingleton().env_singleton

APP_NAME    = "SistemaIntegralCobranza"
LOG_ROUTE   = env.route_log


def _ensure_log_dir():
    """Crea la carpeta de logs si no existe."""
    if LOG_ROUTE and not os.path.exists(LOG_ROUTE):
        os.makedirs(LOG_ROUTE, exist_ok=True)


def logger():
    _ensure_log_dir()

    log = logging.getLogger(APP_NAME)

    if not log.hasHandlers():
        log.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '[%(asctime)s] - [%(filename)s:%(funcName)s:%(lineno)d] - %(levelname)s %(message)s'
        )

        # Handler de archivo con rotación diaria
        today     = date.today().strftime("%Y-%m-%d")
        log_path  = f"{LOG_ROUTE}{APP_NAME}_{today}.log"
        file_handler = TimedRotatingFileHandler(
            log_path, when="midnight", interval=1, backupCount=30
        )
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)

        # Handler de consola (útil en desarrollo)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        log.addHandler(console_handler)

    return log
