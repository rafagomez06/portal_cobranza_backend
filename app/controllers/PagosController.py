from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils.Messages import *
from app.utils.Logger import logger
from app.services.PagosService import PagosService

from app.main import limiter
LOG = logger()
PagosController  = Blueprint("pagos", __name__)

# #####################################
# Rutas privadas (JWT)
# #####################################


@PagosController.route("/registrar-pago", methods=["POST"])
# @jwt_required()
def registrar_pago():
    data = request.form
    files = request.files
    return PagosService.registrar_pago(data, files)

@PagosController.route("/listado-facturas", methods=["GET"])
# @jwt_required()
@limiter.limit("10 per minute")
def listado_facturas():
    data = request.args.to_dict()
    print("DATA ",data)
    return PagosService.listado_facturas(data)



# @PagosController.route("/actualizar-password", methods=["PUT"])
# @jwt_required()
# def actualizar_password():
#     data = request.get_json()
#     return UsuariosService.actualizar_password(data)

# @PagosController.route("/actualizar-permiso-app", methods=["PUT"])
# def actualizar_permiso_app():
#     data = request.get_json()
#     return UsuariosService.actualizar_permiso_app(data)


