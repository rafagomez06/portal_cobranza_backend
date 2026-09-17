from app.models.ChecadorModel import ChecadorModel
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

class ChecadorService:
    @staticmethod
    def registrar_checada(data):
        try:
            LOG.info("## registrar_checada ##")
            
            # Obtenemos valores de peticion
            usuario_id = data["usuario_id"]
            tipo_checada = data["tipo_checada"]
            fecha_hora_captura=data["fecha_hora_captura"]
            id_local=data["id_local"]

            # valores ubicacion
            ubicacion = data.get("ubicacion", {})
            latitud = ubicacion.get("latitud")
            longitud = ubicacion.get("longitud")
            direccion = ubicacion.get("direccionCompleta", {})

            # Validamos tenga la dirección completa
            if direccion is not None:
                direccionCompleta = direccion.get("direccionCompleta", {})
            else:
                direccionCompleta = ""

            #Envio de datos a SP
            checada_result = ChecadorModel.registrar_checada(usuario_id,tipo_checada,latitud,longitud,
                                                            direccionCompleta,fecha_hora_captura,id_local)

            # Convertimos valores obtenidos
            columns = checada_result.keys()
            rows = checada_result.fetchall()
            df_result = pd.DataFrame(rows, columns=columns)
            json_result = df_result.to_json(orient="records")
            
            json_data = []
            # Procesar el resultado del SP
            json_data = json.loads(json_result)
            primer_elemento_sql = json_data[0]
            estadoSQL = primer_elemento_sql.get('estatus')
            mensajeSQL = primer_elemento_sql.get('mensaje')

            # si SP falla se retorna su respuesta
            if estadoSQL != STATUS_CODE_200:
                LOG.info(f"Error: {mensajeSQL} ")
                # ConnectionDb.alchemy_db.session.rollback()
                return api_response(STATUS_CODE_400,{},ERROR,mensajeSQL)
            
            #Commit y Retorno de datos
            ConnectionDb.alchemy_db.session.commit()
            return api_response(STATUS_CODE_200,json_data,SUCCESS,mensajeSQL)

        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Error al realizar la sentencia en registrar_checada:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Error al realizar la sentencia SQL - registrar_checada")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en registrar_checada: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - registrar_checada")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - registrar_checada")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - registrar_checada")        
        
    @staticmethod
    def obtener_historial_checadas(data):
        try:
            LOG.info("## obtener_historial_checadas ##")
            # Obtenemos valores de peticion
            usuario_id = data["usuario_id"]
            rango_fecha_inicio = data["rango_fecha_inicio"]
            rango_fecha_fin = data["rango_fecha_fin"]

            listado_result = ChecadorModel.obtener_historial_checadas(usuario_id,rango_fecha_inicio,rango_fecha_fin)

            # Convertimos valores obtenidos
            columns = listado_result.keys()
            rows = listado_result.fetchall()

            # Validamos resultado
            if columns is None or len(rows) == 0:
                LOG.info(f"GET /historial-checadas")
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
                f"Err al realizar la sentencia en obtener_historial_checadas:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en obtener_historial_checadas: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - obtener_historial_checadas")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - obtener_historial_checadas")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - obtener_historial_checadas")
    
    @staticmethod
    def obtener_bitacora_checadas_detalle(data):
        try:
            LOG.info("## obtener_bitacora_checadas_detalle ##")
            usuario_id = data.get("usuario_id","")  
            rango_fecha_inicio = data.get("rango_fecha_inicio","")  
            rango_fecha_fin = data.get("rango_fecha_fin","")
            id_empresa = data.get("id_empresa","")
            generar_pdf = data.get("generar_pdf",0)
            pagina = data.get("pagina",1)

            # Validamos y enviamos vacio si no viene con valores
            usuario_id = usuario_id if usuario_id else ''
            rango_fecha_inicio = rango_fecha_inicio.strip() if rango_fecha_inicio else ''
            rango_fecha_fin = rango_fecha_fin.strip() if rango_fecha_fin else ''
            id_empresa = id_empresa if id_empresa else ''
            pagina = pagina if pagina else 1

            listado_result = ChecadorModel.obtener_bitacora_checadas_detalle(usuario_id,rango_fecha_inicio,rango_fecha_fin,
                                                                            id_empresa,pagina)

            # Convertimos valores obtenidos
            columns = listado_result.keys()
            rows = listado_result.fetchall()

            # Validamos resultado
            if columns is None or len(rows) == 0:
                LOG.info(f"GET /bitacora-checadas-detalle")
                return api_response(STATUS_CODE_404, [],ERROR,ERROR_EMPTY)

            df_result = pd.DataFrame(rows, columns=columns)
            # Obtenemos registros de fechas para formatear como 'YYYY-MM-DD HH:mm:ss'
            df_result["fecha_registro"] = pd.to_datetime(df_result["fecha_registro"])
            df_result["fecha_captura_dispositivo"] = pd.to_datetime(df_result["fecha_captura_dispositivo"])
            df_result["fecha_jornada"] = pd.to_datetime(df_result["fecha_jornada"])

            # Formateo fechas
            df_result["fecha_registro"] = df_result["fecha_registro"].dt.strftime("%Y-%m-%d %H:%M:%S")
            df_result["fecha_captura_dispositivo"] = df_result["fecha_captura_dispositivo"].dt.strftime("%Y-%m-%d %H:%M:%S")

            df_result["fecha_jornada"] = df_result["fecha_jornada"].dt.strftime("%Y-%m-%d")
            # Obtener registros como diccionario
            registros = df_result.to_dict(orient="records")

            # Convertimos las filas de datos en una lista de diccionarios
            datos_agrupados = ChecadorService.agrupar_por_usuario(registros)
            total_agrupados = len(datos_agrupados) 

            # Genera PDF
            if (generar_pdf == "1"):
                titulo = "Reporte de Checadas App"
                pdf_bytes = PDFService.generar_pdf_checadas(datos_agrupados, titulo,rango_fecha_inicio,rango_fecha_fin,id_empresa)
                
                # Crear respuesta con el PDF
                response = send_file(
                    io.BytesIO(pdf_bytes),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f'reporte_checadas_app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                )
                return response

            # Flujo normal
            msj = f"{total_agrupados} Empleado(s) encontrado(s)"

            return api_response(STATUS_CODE_200,datos_agrupados,SUCCESS,msj)

        except Exception as e:
                LOG.error(f"Error generando PDF: {e}")
                return api_response(
                    STATUS_CODE_500,
                    [],
                    ERROR,
                    "Error al generar el PDF"
                ), 500
        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en obtener_bitacora_checadas_detalle:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en obtener_bitacora_checadas_detalle: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - obtener_bitacora_checadas_detalle")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - obtener_bitacora_checadas_detalle")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - obtener_bitacora_checadas_detalle")

    @staticmethod
    def agrupar_por_usuario(datos):
        # Validar si esta vacía
        if not datos:
            return []
        
        usuarios_dict = {}
        
        for registro in datos:
            id_usuario = registro.get("id_usuario")
            id_empresa = registro.get("id_empresa")
            nombre_empresa = registro.get("nombre_empresa")
            fecha_jornada = registro.get("fecha_jornada")
            pagina = registro.get("pagina")

            
            if id_usuario not in usuarios_dict:
                usuarios_dict[id_usuario] = {
                    "id_usuario": id_usuario,
                    "nombre_completo": str(registro.get("nombre_completo", "")).strip(),
                    "id_empresa": id_empresa,
                    "nombre_empresa": nombre_empresa,
                    "pagina:":pagina,
                    "detalle_checadas": []
                }
            
            detalle = {
                "id_jornada": registro.get("id_jornada"),
                "id_tipo_checada": registro.get("id_tipo_checada"),
                "tipo_checada_descripcion": registro.get("tipo_checada_descripcion"),
                "dia_semana": registro.get("dia_semana"),
                "coordenadas_latitud": registro.get("coordenadas_latitud"),
                "coordenadas_longitud": registro.get("coordenadas_longitud"),
                "direccion_ubicacion": registro.get("direccion_ubicacion"),
                "fecha_jornada": registro.get("fecha_jornada"),
                "fecha_registro": registro.get("fecha_registro"),
                "fecha_captura_dispositivo": registro.get("fecha_captura_dispositivo"),
                "checada_UUID": registro.get("checada_UUID"),
                "num_registro": registro.get("num_registro")
            }
            
            usuarios_dict[id_usuario]["detalle_checadas"].append(detalle)
        
        # Ordenar los detalles por fecha_registro dentro de cada usuario
        for usuario in usuarios_dict.values():
            usuario["detalle_checadas"] = sorted(
                usuario["detalle_checadas"],
                key=lambda x: str(x.get("fecha_registro", ""))
            )
        
        # Convertir a lista y ordenar por num empleado
        usuarios_lista = list(usuarios_dict.values())
        usuarios_lista.sort(key=lambda x: x.get("id_usuario", ""))
        
        return usuarios_lista