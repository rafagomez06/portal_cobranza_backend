from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils.Messages import *
from app.utils.Logger import logger
from app.services.ChecadorService import ChecadorService
from app.main import limiter

LOG = logger()
ChecadorController  = Blueprint("checador", __name__)

# #####################################
# Rutas privadas (JWT)
# #####################################

# Checada Normal con conexión
@ChecadorController.route("/registrar-checada", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
def registrar_checada():
    data = request.get_json()
    return ChecadorService.registrar_checada(data)

@ChecadorController.route("/historial-checadas", methods=["GET"])
@jwt_required()
@limiter.limit("10 per minute")
def obtener_historial_checadas():
    data = request.args.to_dict()
    return ChecadorService.obtener_historial_checadas(data)

@ChecadorController.route("/bitacora-checadas-detalle", methods=["GET"])
@limiter.limit("10 per minute")
def obtener_bitacora_checadas_detalle():
    data = request.args.to_dict()
    return ChecadorService.obtener_bitacora_checadas_detalle(data)
