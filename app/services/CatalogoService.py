
from app.models.CatalogoModel import CatalogoModel
from app.utils.response import api_response
from app.utils.RaiseException import UnexpectedError
from app.utils.Logger import logger
from app.services.pdfService import PDFService
from flask import send_file
import io
from datetime import datetime
import traceback
import json
import pandas as pd
from app.utils.RaiseException import ( DatabaseError,  UnexpectedError)
from app.utils.Messages import *
from sqlalchemy import exc
from app.main import ConnectionDb

LOG = logger()

class CatalogoService:

    @staticmethod
    def obtener_tipos_facturas(data):
        try:
            LOG.info("## obtener_tipos_facturas ##")
            
            clv_tipo = data["clv_tipo"]

            # Normaliza: None si no hay valor, si es None, o si es cadena vacía
            if clv_tipo is None:
                clv_tipo = None
            else:
                clv_tipo = str(clv_tipo).strip()
                clv_tipo = clv_tipo if clv_tipo != "" else ""

            listado_result = CatalogoModel.obtener_tipos_facturas(clv_tipo)
            # Convertimos valores obtenidos
            columns = listado_result.keys()
            rows = listado_result.fetchall()

            # Validamos resultado
            if columns is None or len(rows) == 0:
                LOG.info(f"GET /catalogo/tipos-facturas")
                return api_response(STATUS_CODE_404, [],ERROR,ERROR_EMPTY)

            df_result = pd.DataFrame(rows, columns=columns)

            # Limpiar t_body antes de asignar nuevos valores
            t_body = []

            # Convertimos las filas de datos en una lista de diccionarios
            t_body = df_result.to_dict(orient="records")
            
            return api_response(STATUS_CODE_200,t_body,SUCCESS)

        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en obtener_tipos_facturas:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en obtener_tipos_facturas: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - obtener_tipos_facturas")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - obtener_tipos_facturas")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - obtener_tipos_facturas")
    
