from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils.Messages import *
from app.utils.Logger import logger
from app.services.CatalogoService import CatalogoService

from app.main import limiter

LOG = logger()
CatalogosController  = Blueprint("catalogo", __name__)

# #####################################
# Rutas privadas (JWT)
# #####################################

# Checada Normal con conexión
# @CatalogosController.route("/registrar-checada", methods=["POST"])
# @jwt_required()
# @limiter.limit("10 per minute")
# def registrar_checada():
#     data = request.get_json()
#     return ChecadorService.registrar_checada(data)

@CatalogosController.route("/tipos-facturas", methods=["GET"])
#@jwt_required()
@limiter.limit("10 per minute")
def obtener_tipos_facturas():
    data = request.args.to_dict()
    return CatalogoService.obtener_tipos_facturas(data)
