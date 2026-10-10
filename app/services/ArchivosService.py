
import os
from flask import Flask, send_from_directory, abort
from app.utils.response import api_response
from app.utils.RaiseException import UnexpectedError
from app.utils.Logger import logger
import traceback
import json
import pandas as pd
from app.utils.RaiseException import ( DatabaseError,  UnexpectedError)
from app.utils.Messages import *
from app.main import ConnectionDb
from app.utils.FileTools import FileTools  

from sqlalchemy import exc

LOG = logger()

class ArchivosService:
    @staticmethod
    def obtener_archivo(data):
        try:
            LOG.info("## obtener_archivo ##")
            factura = data["factura"].strip()

            result_archivo = FileTools.obtener_ruta_factura(factura)
            archivo_encontrado = result_archivo["archivo_encontrado"]
            ruta_factura = result_archivo['ruta_factura']
            nombre_archivo = result_archivo['nombre_archivo']
            
            # Valida si exite la factura
            if not archivo_encontrado:
                return api_response(STATUS_CODE_404,None,ERROR,SIN_FACTURA)

            # send_from_directory sirve el archivo de forma segura
            return send_from_directory(
                ruta_factura, 
                nombre_archivo, 
                as_attachment=False,  # True para forzar descarga / False para visualizar en el navegador.
                mimetype="application/pdf",
            )

        except exc.StatementError as sta_err:
                LOG.error(f"Err al realizar la sentencia en obtener_archivo: {str(sta_err)} [{traceback.format_exc()}]")
                raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e:
            LOG.error(f"DB error en obtener_archivo: {str(e)} [{traceback.format_exc()}]")
            raise DatabaseError("Error al consultar la base de datos - obtener_archivo")
        except ValueError as e:
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - obtener_archivo")   