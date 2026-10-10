from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils.Messages import *
from app.utils.Logger import logger
from app.services.ArchivosService import ArchivosService
from app.main import limiter
LOG = logger()
ArchivosController  = Blueprint("archivo", __name__)
# #####################################
# Rutas privadas (JWT)
# #####################################

@ArchivosController.route("/obtener-archivo", methods=["GET"])
@jwt_required()
def obtener_archivo():
    data = request.args.to_dict()
    return ArchivosService.obtener_archivo(data)
