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

@CatalogosController.route("/tipos-facturas", methods=["GET"])
@jwt_required()
def obtener_tipos_facturas():
    data = request.args.to_dict()
    return CatalogoService.obtener_tipos_facturas(data)
