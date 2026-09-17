from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils.Messages import *
from app.utils.Logger import logger
from app.services.UsuariosService import UsuariosService
from app.main import limiter
LOG = logger()
UsuariosController  = Blueprint("usuarios", __name__)

# #####################################
# Rutas privadas (JWT)
# #####################################

@UsuariosController.route("/login", methods=["POST"])
# @jwt_required()
def validar_login():
    data = request.get_json()
    return UsuariosService.validar_login(data)

@UsuariosController.route("/registrar-usuario", methods=["POST"])
def registrar_usuario():
    data = request.get_json()
    return UsuariosService.registrar_usuario(data)

@UsuariosController.route("/actualizar-password", methods=["PUT"])
@jwt_required()
def actualizar_password():
    data = request.get_json()
    return UsuariosService.actualizar_password(data)

@UsuariosController.route("/actualizar-permiso-app", methods=["PUT"])
def actualizar_permiso_app():
    data = request.get_json()
    return UsuariosService.actualizar_permiso_app(data)

@UsuariosController.route("/listado-usuarios", methods=["GET"])
# @jwt_required()
@limiter.limit("10 per minute")
def listado_usuarios():
    data = request.args.to_dict()
    return UsuariosService.listado_usuarios(data)
