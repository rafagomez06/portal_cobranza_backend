from app.models.CorreoModel import CorreoModel
from datetime import datetime
from flask import render_template
from flask_jwt_extended import create_access_token
from app.utils.FormateoData import formato_moneda
from app.utils.response import api_response
from app.utils.RaiseException import UnexpectedError
from app.utils.Logger import logger
import traceback
import json
import pandas as pd
from app.utils.RaiseException import ( DatabaseError,  UnexpectedError)
from app.utils.Messages import *
from app.utils.PassConvert import set_password,check_password
from app.main import ConnectionDb
from app.utils.FileTools import FileTools  
from app.utils.mailer import enviar_correo

from sqlalchemy import exc

LOG = logger()

class CorreoService:
    @staticmethod
    def enviar_correo(data):
        try:
            para=data.get("para", "")
            asunto=data.get("asunto", "")
            #cuerpo=data.get("cuerpo", "")
            lista_archivo=data.get("lista_archivo", [])  # lista de rutas
            cod_autenticacion=data.get("cod_autenticacion", 0)
            usar_hostgator=data.get("usar_hostgator", False)
            copia_a=data.get("copia_a", "")
            bcc=data.get("bcc", "")
            identificador=data.get("identificador", "")
            pantalla=data.get("pantalla", "")
            empresa=data.get("empresa", "")
            enviar_flag=data.get("enviar_correo", True)
            ordenes=data.get("ordenes", "")

            template_name = data.get("template_name")
            if template_name:
                # Diccionario con las variables que requiere el template
                template_data = data.get("template_data", {})
                
                template_data.setdefault("anio_actual", datetime.now().year)
                # Renderiza la plantilla HTML pasándole los datos
                cuerpo = render_template(template_name, **template_data)
            else:
                # Si no se define plantilla, utiliza el cuerpo que viene en string plano/HTML
                cuerpo = data.get("cuerpo", "")
            resultado = enviar_correo(
                        para,asunto,cuerpo,lista_archivo,cod_autenticacion,usar_hostgator,copia_a,bcc,identificador,pantalla,
                        empresa,enviar_flag,ordenes)
            

            if resultado != "":
                return api_response(STATUS_CODE_500,[],ERROR,'Ocurrio un error al enviar correo')

            # Exito
            return api_response(STATUS_CODE_200,[],SUCCESS,'Correo enviado')
        
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en enviar_correo: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - enviar_correo")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - enviar_correo")     
