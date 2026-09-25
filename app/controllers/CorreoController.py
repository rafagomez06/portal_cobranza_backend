from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils.Messages import *
from app.utils.Logger import logger
from app.services.CorreoService import CorreoService
from app.utils.response import api_response
from app.main import limiter

LOG = logger()
CorreoController  = Blueprint("correo", __name__)

# #####################################
# Rutas privadas (JWT)
# #####################################

@CorreoController.route("/enviar-correo", methods=["POST"])
#@jwt_required()
def enviar_correo():
    data = request.get_json(force=True)
    return CorreoService.enviar_correo(data)

