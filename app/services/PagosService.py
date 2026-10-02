import json

from app.models.PagosModel import PagosModel
from app.utils.FormateoData import formato_moneda,_trim
from app.utils.response import api_response
from app.utils.RaiseException import UnexpectedError
from app.utils.Logger import logger
import traceback
import json
import pandas as pd
from app.utils.RaiseException import ( DatabaseError,  UnexpectedError)
from app.utils.Messages import *
from app.main import ConnectionDb
from app.models.UsuariosModel import UsuariosModel

from app.utils.FileTools import FileTools  

from sqlalchemy import exc

LOG = logger()

class PagosService:
    # Registra un nuevo pago
    @staticmethod
    def registrar_pago(data,files):
        try:
            # Obtenemos valores 
            cod_empresa = data.get("cod_empresa")
            rfc_cliente = data.get("rfc_cliente")
            cod_cliente = data.get("cod_cliente")
            moneda = data.get("moneda")
            importe_monto = data.get("importe_monto")
            importe_disponible = data.get("importe_disponible")
            importe_abonado = data.get("importe_abonado")
            comprobante_file = files['comprobante_file']
            # Detalle de facturas seleccionadas
            facturas_str = data.get("facturas", "[]")

            # Validación si no llegan las facturas
            if not facturas_str:
                return api_response(STATUS_CODE_400,{},ERROR,FACTURAS_VACIAS)
            
            # parsear el JSON recibido
            try:
                facturas = json.loads(facturas_str)
            except json.JSONDecodeError:
                # falla el JSON o esta mal formado, fallback a lista vacía
                facturas = []

            facturas_data = [
                {
                    'orden': item.get('orden'),
                    'factura': item.get('factura'),
                    'tipo_moneda': item.get('tipo_moneda'),
                    'importe_factura': float(item.get('importe_factura', 0)),  
                    'importe_abonado': float(item.get('importe_abonado', 0)),
                    'importe_abonar': float(item.get('importe_abonar', 0)),
                    'saldo_pendiente': float(item.get('saldo_pendiente_factura', 0))
                }
                for item in facturas
            ]

            # Guardamos ruta del archivo
            info_archivo = FileTools.guardar_archivo_cobranza(comprobante_file,cod_cliente,rfc_cliente)
            ruta_completa = info_archivo['ruta_completa']
            ip_servidor_archivo = info_archivo['ip_servidor_archivo']
            ruta_archivo = info_archivo['ruta_comprobante']
            carpeta_padre = info_archivo['carpeta_padre']
            nombre_archivo = info_archivo['nombre_archivo']

            # Si no retorna información, falló extensión
            if not info_archivo:
                return api_response(STATUS_CODE_400,[],ERROR,FILE_ERROR)

            # Envio de datos a BD Registrar en tabla Cabecero
            registrar_pago_result = PagosModel.registrar_pago(cod_empresa,cod_cliente,rfc_cliente,moneda
                                                            ,importe_monto,importe_disponible,importe_abonado)
            # Convertimos valores obtenidos
            rows_pago = [dict(row._mapping) for row in registrar_pago_result.fetchall()] if registrar_pago_result else []
            if not rows_pago:
                return api_response(STATUS_CODE_404, [],ERROR,"El SP sp_RegistrarPagos_SIC no retornó respuesta.")
            
            # Procesar el resultado del SP sp_RegistrarPagos_SIC
            primer_elemento_sql = rows_pago[0]
            estadoSQL = primer_elemento_sql.get('estatus')
            mensajeSQL = primer_elemento_sql.get('mensaje')
            idPagoSQL = primer_elemento_sql.get('id_pago')
            # Obtenemos ID generado
            id_generado = {"id_generado":idPagoSQL}

            # si SP falla se retorna su respuesta
            if estadoSQL != STATUS_CODE_200:
                LOG.info(f"Error: {mensajeSQL} ")
                PagosService.limpiar_recursos(ruta_completa)
                return api_response(STATUS_CODE_400,{},ERROR,mensajeSQL)

            # Envio de datos a BD del Archivo
            registrar_archivo_pago_result = PagosModel.registrar_comprobante_pago(idPagoSQL,ip_servidor_archivo,ruta_archivo,
                                                                    carpeta_padre,nombre_archivo)
            # Convertimos valores obtenidos
            rows_archivo = [dict(row._mapping) for row in registrar_archivo_pago_result.fetchall()] if registrar_archivo_pago_result else []
            if not rows_archivo:
                return api_response(STATUS_CODE_404, [],ERROR,"El SP sp_RegistrarComprobantePago_SIC no retornó respuesta.")

            # Procesar el resultado del SP sp_RegistrarComprobantePago_SIC
            primer_elemento_sql = rows_archivo[0]
            estadoSQL = primer_elemento_sql.get('estatus')
            mensajeSQL = primer_elemento_sql.get('mensaje')

            # si SP falla se retorna su respuesta
            if estadoSQL != STATUS_CODE_200:
                LOG.info(f"Error: {mensajeSQL} ")
                PagosService.limpiar_recursos(ruta_completa)
                return api_response(STATUS_CODE_400,{},ERROR,mensajeSQL)

            # Guardamos en tabla de detalle 
            registrar_pago_det_result = PagosModel.registrar_pago_detalle(idPagoSQL,facturas_data)
            
            # Convertimos valores obtenidos
            rows_detalle = [dict(row._mapping) for row in registrar_pago_det_result.fetchall()] if registrar_pago_det_result else []
            if not rows_detalle:
                return api_response(STATUS_CODE_404, [],ERROR,"El SP sp_RegistrarPagosDetalle_SIC no retornó respuesta.")                
            
            # Procesar el resultado del SP sp_RegistrarPagosDetalle_SIC
            primer_elemento_sql = rows_detalle[0]
            estadoSQL = primer_elemento_sql.get('estatus')
            mensajeSQL = primer_elemento_sql.get('mensaje')
            
            # si SP falla se retorna su respuesta
            if estadoSQL != STATUS_CODE_200:
                LOG.info(f"Error: {mensajeSQL} ")
                PagosService.limpiar_recursos(ruta_completa)
                return api_response(STATUS_CODE_400,{},ERROR,mensajeSQL)
            
            # Commit a registros insertados
            ConnectionDb.alchemy_db.session.commit()

            return api_response(STATUS_CODE_200,id_generado,SUCCESS,mensajeSQL)
        
        except exc.StatementError as sta_err:
                PagosService.limpiar_recursos(ruta_completa)
                LOG.error(f"Err al realizar la sentencia en registrar_pago: {str(sta_err)} [{traceback.format_exc()}]")
                raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e:
            PagosService.limpiar_recursos(ruta_completa)
            LOG.error(f"DB error en registrar_pago: {str(e)} [{traceback.format_exc()}]")
            raise DatabaseError("Error al consultar la base de datos - registrar_pago")
        except ValueError as e:
            PagosService.limpiar_recursos(ruta_completa)
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:
            PagosService.limpiar_recursos(ruta_completa)
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - registrar_pago")    

    @staticmethod
    def listado_facturas(data):
        try:
            LOG.info("## listado_facturas ##")
            rfc_cliente = data["rfc"].strip()
            moneda = data["moneda"].strip()
            # Busca el codigo del cliente primero
            codigo_result = UsuariosModel.obtener_codigo_cliente(rfc_cliente,moneda)

            # Convertimos valores obtenidos
            rows_facturas = [dict(row._mapping) for row in codigo_result.fetchall()] if codigo_result else []
            if not rows_facturas:
                return api_response(STATUS_CODE_404, [],ERROR,"El SP sp_ObtenerCodCliente_SIC no retornó respuesta.")
            
            # Procesar el resultado del SP Codigo Empleado
            primer_elemento_sql = rows_facturas[0]
            idUsuarioSQL = primer_elemento_sql.get('id_usuario')
            codClienteSQL = _trim(primer_elemento_sql.get('cod_cliente'))
            nomClienteSQL = _trim(primer_elemento_sql.get('nom_cliente'))
            rfcClienteSQL = _trim(primer_elemento_sql.get('rfc_cte'))
            monedaClienteSQL = _trim(primer_elemento_sql.get('moneda'))
            correoClienteSQL = _trim(primer_elemento_sql.get('correo'))

            # Buscamos facturas del codCliente
            listado_result = PagosModel.obtener_facturas(codClienteSQL)
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
            df_result["fecha_vencimiento"] = pd.to_datetime(df_result["fecha_vencimiento"])
            df_result["importe_factura"] = df_result["importe_factura"].apply(formato_moneda)
            df_result["importe_abonar"] = df_result["importe_abonar"].apply(formato_moneda)
            df_result["saldo_pendiente_factura"] = df_result["saldo_pendiente_factura"].apply(formato_moneda)

            # Formateo fechas
            df_result["fecha"] = df_result["fecha"].dt.strftime("%Y-%m-%d")
            df_result["fecha_vencimiento"] = df_result["fecha_vencimiento"].dt.strftime("%Y-%m-%d")

            total_registros = len(df_result) 
            # Limpiar variables antes de asignar nuevos valores
            t_body = []
            t_head = []

            t_head = [
                {"dataIndex": col, "key": col, "title": col.replace("_", " ").capitalize()}
                for col in columns
            ]
            # Convertimos las filas de datos en una lista de diccionarios
            t_body = df_result.to_dict(orient="records")
            msj = f"{total_registros} Facturas(s) encontrada(s)"

            # resultado
            data = {
                "t_header":t_head,
                "t_body":t_body,
                "id_usuario": idUsuarioSQL,
                "cod_cliente": codClienteSQL,
                "nom_cliente": nomClienteSQL,
                "rfc_cte": rfcClienteSQL,
                "moneda": monedaClienteSQL,
                "correo": correoClienteSQL
            }
            return api_response(STATUS_CODE_200,data,SUCCESS,msj)
        
        except exc.StatementError as sta_err:
                LOG.error(f"Err al realizar la sentencia en listado_facturas: {str(sta_err)} [{traceback.format_exc()}]")
                raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e:
            LOG.error(f"DB error en listado_facturas: {str(e)} [{traceback.format_exc()}]")
            raise DatabaseError("Error al consultar la base de datos - listado_facturas")
        except ValueError as e:
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - listado_facturas")   

    #Metodo auxiliar para hacer rollback en BD y eliminar archivos de forma segura.
    @staticmethod
    def limpiar_recursos(ruta_completa):
        try:
            ConnectionDb.alchemy_db.session.rollback()
        except Exception as e:
            LOG.error(f"Error al intentar hacer rollback de la sesión: {str(e)}")
        if ruta_completa:
            try:
                FileTools.elimina_archivo_ruta(ruta_completa)
            except Exception as e:
                LOG.warning(f"No se pudo eliminar el archivo temporal en '{ruta_completa}': {str(e)}")        