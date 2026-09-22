import os
from datetime import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded

from app.utils.response import api_response
from app.utils.Messages import *

def get_limiter_key():
    return get_remote_address()

# Extensiones se instancian sin app (patron Application Factory)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://" # En producción cambia a Redis: "redis://localhost:6379"
)
# Mensaje Personalizado retorno token expirado
@jwt.expired_token_loader
def token_expirado_callback(jwt_header, jwt_payload):
    return jsonify({
        "body": {
            "status_code": STATUS_CODE_401,
            "status_message": "token_expired",
            "message": "El token ha expirado. Por favor, vuelve a iniciar sesión.",
            "data": None
        }
    }), 401
class ConnectionDb:
    _instance = None
    alchemy_db = db

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

def create_app(env: str = "default") -> Flask:
    from app.config import config

    app = Flask(__name__)

    app.config.from_object(config[env])
    app.json.sort_keys = False
    # Inicializar extensiones 
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    

    # CORS(app, origins=["http://localhost:3000"])   # Consumo de Front en desarrollo
    CORS(app, origins="*")  # Permitir todos
    URL_PREFIX = '/api/v1/sic' # Sistema Integral Cobranza

    # Registrar Rutas de entrada 
    from app.controllers.CatalogosController import CatalogosController
    from app.controllers.UsuariosController import UsuariosController
    from app.controllers.PagosController import PagosController

    # Rutas Endpoints
    app.register_blueprint(UsuariosController, url_prefix=f"{URL_PREFIX}/auth")
    app.register_blueprint(CatalogosController, url_prefix=f"{URL_PREFIX}/catalogo")
    app.register_blueprint(PagosController, url_prefix=f"{URL_PREFIX}/pago")


    # Manejadores de errores globales 
    _register_error_handlers(app)

    # HEALT CHECK ENDPOINT
    @app.route('/api/v1/sic/health', methods=['GET'])
    @limiter.limit("5 per minute")
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Sistema Integral Cobranza(SIC) - API",
            "version": "1.0.0",
            "mensaje": "Funcionando OK",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    return app

def _register_error_handlers(app: Flask):
    """Registra los manejadores de excepciones personalizadas."""
    from app.utils.RaiseException import (
        DatabaseError, MissingValueError, NotFoundError,
        UnexpectedError, UnauthorizedError, FileUploadError
    )
    from app.utils.Logger import logger
    LOG = logger()


    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(error):
        LOG.warning(f"RateLimitExceeded: {error.description}")
        return api_response(
            STATUS_CODE_429 if 'STATUS_CODE_429' in globals() else 429,
            [],
            ERROR,
            f"Límite de peticiones superado: {error.description}"
        )

    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        LOG.error(f"DatabaseError: {error}")
        return api_response(STATUS_CODE_500,[],ERROR,str(error))

    @app.errorhandler(MissingValueError)
    def handle_missing_value(error):
        LOG.warning(f"MissingValueError: {error}")
        return api_response(STATUS_CODE_400,[],ERROR,str(error))

    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        LOG.warning(f"NotFoundError: {error}")
        return api_response(STATUS_CODE_404,[],ERROR,str(error))

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized(error):
        LOG.warning(f"UnauthorizedError: {error}")
        print(f"UnauthorizedError: {error}")
        return api_response(STATUS_CODE_401,[],ERROR,str(error))

    @app.errorhandler(FileUploadError)
    def handle_file_upload(error):
        LOG.error(f"FileUploadError: {error}")
        return api_response(STATUS_CODE_400,[],ERROR,str(error))

    @app.errorhandler(UnexpectedError)
    def handle_unexpected(error):
        LOG.error(f"UnexpectedError: {error}")
        return api_response(STATUS_CODE_500,[],ERROR,"Ocurrió un error inesperado")

    @app.errorhandler(404)
    def not_found(error):
        return api_response(STATUS_CODE_404,[],ERROR,"Ruta no encontrada")

    @app.errorhandler(405)
    def method_not_allowed(error):
        return api_response(STATUS_CODE_405,[],ERROR,"Método no permitido")
