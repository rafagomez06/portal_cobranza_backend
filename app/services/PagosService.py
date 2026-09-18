from app.models.PagosModel import PagosModel
from flask_jwt_extended import create_access_token
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

from sqlalchemy import exc

LOG = logger()

class PagosService:
    # Registra un nuevo pago
    @staticmethod
    def registrar_pago(data,files):
        try:
            LOG.info("## registrar_pago ##")
            # Obtenemos valores 
            cod_cliente = data.get("cod_cliente")
            nom_cliente = data.get("nom_cliente")
            comprobante_file = files['comprobante_file']

            # Guardamos ruta del archivo
            ruta_archivo = FileTools.guardar_archivo_cobranza(comprobante_file)
            # Si no retorna información, falló extensión
            if not ruta_archivo:
                return api_response(STATUS_CODE_400,None,ERROR,FILE_ERROR)


            
            #Envio de datos a BD
            # registrar_result = PagosService.registrar_pago(id_empleado,
            #                                                 id_empresa,usuario_checador,nombre
            #                                                 ,apellido_paterno
            #                                                 ,apellido_materno,correo,usuario_creacion)

            return api_response(STATUS_CODE_200,'mensajeSQL',SUCCESS,'')
        
        except exc.StatementError as sta_err:
            FileTools.elimina_archivo_ruta(ruta_archivo)
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en registrar_pago:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            FileTools.elimina_archivo_ruta(ruta_archivo)
            LOG.error(f"DB error en registrar_pago: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - registrar_pago")
        except ValueError as e: 
            FileTools.elimina_archivo_ruta(ruta_archivo)
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:  
            FileTools.elimina_archivo_ruta(ruta_archivo)
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - registrar_pago")     

    @staticmethod
    def listado_facturas(data):
        try:
            LOG.info("## listado_facturas ##")
            cod_cliente = data["cod_cliente"].strip()
            listado_result = PagosModel.obtener_facturas(cod_cliente)

            # Convertimos valores obtenidos
            columns = listado_result.keys()
            rows = listado_result.fetchall()

            # Validamos resultado
            if columns is None or len(rows) == 0:
                LOG.info(f"GET /listado-facturas")
                return api_response(STATUS_CODE_404, [],ERROR,ERROR_EMPTY)
            
            # Resultados
            df_result = pd.DataFrame(rows, columns=columns)
            # Obtenemos registros de fechas para formatear como 'YYYY-MM-DD'
            df_result["fecha"] = pd.to_datetime(df_result["fecha"])
            df_result["fecha_vence"] = pd.to_datetime(df_result["fecha_vence"])

            # Formateo fechas
            df_result["fecha"] = df_result["fecha"].dt.strftime("%Y-%m-%d")
            df_result["fecha_vence"] = df_result["fecha_vence"].dt.strftime("%Y-%m-%d")

            total_registros = len(df_result) 

            # Limpiar t_body antes de asignar nuevos valores
            t_body = []

            # Convertimos las filas de datos en una lista de diccionarios
            t_body = df_result.to_dict(orient="records")
            msj = f"{total_registros} Facturas(s) encontrada(s)"
            
            return api_response(STATUS_CODE_200,t_body,SUCCESS,msj)

        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en listado_facturas:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en listado_facturas: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - listado_facturas")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - listado_facturas")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - listado_facturas")