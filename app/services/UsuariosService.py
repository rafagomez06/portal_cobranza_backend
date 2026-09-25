from app.models.UsuariosModel import UsuariosModel
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

from sqlalchemy import exc

LOG = logger()

class UsuariosService:
    # Registra un nuevo usuario
    @staticmethod
    def registrar_usuario(data):
        try:
            LOG.info("## registrar_usuario ##")
            # Obtenemos valores 
            cod_cliente = data["cod_cliente"].strip()
            nom_cliente = data["nom_cliente"].strip()
            rfc_cte = data["rfc_cte"].strip()
            moneda = data["moneda"].strip()
            correo = data["correo"].strip()

            #Envio de datos
            registrar_result = UsuariosModel.registrar_usuario(cod_cliente,
                                                            nom_cliente,rfc_cte,moneda
                                                            ,correo)

            # Convertimos valores obtenidos
            columns = registrar_result.keys()
            rows = registrar_result.fetchall()
            df_result = pd.DataFrame(rows, columns=columns)
            json_result = df_result.to_json(orient="records")
            
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
                f"Err al realizar la sentencia en registrar_usuario:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en registrar_usuario: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - registrar_usuario")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - registrar_usuario")     

    # Valida login de usuario
    @staticmethod
    def validar_login(data):
        try:
            LOG.info("## validar_login ##")
            print(data)
            # Obtenemos valores 
            cod_cliente = data["cod_cliente"].strip()
            correo = data["correo"].strip()
            password = data["password"]

            #Consultamos usuario y validamos
            result_obtener = UsuariosService.obtener_cliente_login(cod_cliente)
            estatus_result = result_obtener["estatus"]
            mensaje_result = result_obtener["mensaje"]
            password_hash_result = result_obtener["password_hash"]

            if estatus_result != STATUS_CODE_200:
                LOG.info(f"{mensaje_result}: {cod_cliente}")
                return api_response(STATUS_CODE_401,{},LOGIN_FAILED,mensaje_result)

            #Valida si pass es correcto
            es_pass_valido = check_password(password_hash_result, password)

            if not es_pass_valido:
                LOG.info(f"Contraseña incorrecta para el cliente: {cod_cliente}")
                return api_response(STATUS_CODE_401,{},LOGIN_FAILED,CREDENCIALES_FALLIDAS)
            
            #Validamos login
            valida_result = UsuariosModel.validar_login(cod_cliente,correo,password_hash_result)

            # Convertimos valores obtenidos
            columns = valida_result.keys()
            rows = valida_result.fetchall()
            df_result = pd.DataFrame(rows, columns=columns)
            json_result = df_result.to_json(orient="records")
            
            # Procesar el resultado del SP
            json_data = json.loads(json_result)
            primer_elemento_sql = json_data[0]
            estadoSQL = primer_elemento_sql.get('estatus')
            mensajeSQL = primer_elemento_sql.get('mensaje')
            cod_clienteSQL = primer_elemento_sql.get('cod_cliente')
            nom_clienteSQL = primer_elemento_sql.get('nom_cliente')
            correo_clienteSQL = primer_elemento_sql.get('correo')
            id_clienteSQL = primer_elemento_sql.get('id_cliente')

            # si SP falla se retorna su respuesta
            if estadoSQL != STATUS_CODE_200:
                LOG.info(f"Error: {mensajeSQL} ")
                # ConnectionDb.alchemy_db.session.rollback()
                return api_response(STATUS_CODE_400,{},LOGIN_FAILED,mensajeSQL)

            cliente_key = (cod_clienteSQL + correo_clienteSQL+password_hash_result)
            # Generamos token unico
            token = create_access_token(identity=str(cliente_key))

            t_body = []

            # Convertimos las filas de datos en una lista de diccionarios
            t_body = {
                    "token": token,
                    "cod_cliente":cod_clienteSQL,
                    "nom_cliente":nom_clienteSQL,
                    "correo_cliente":correo_clienteSQL,
                    "id_cliente":id_clienteSQL
                    }

            #Commit y Retorno de datos
            return api_response(STATUS_CODE_200,t_body ,SUCCESS,mensajeSQL)

        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en validar_login:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL - validar_login")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en validar_login: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - validar_login")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - validar_login")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - validar_login")       

    # Obtiene la pass de cliente hasheada (encriptada)
    @staticmethod
    def obtener_cliente_login(cliente):
        try:
            LOG.info("## obtener_cliente_login ##")

            # Obtenemos valores 
            result = UsuariosModel.obtener_cliente_login(cliente)

            # Convertimos valores obtenidos
            columns = result.keys()
            rows = result.fetchall()
            df_result = pd.DataFrame(rows, columns=columns)
            json_result = df_result.to_json(orient="records")
            
            # Procesar el resultado del SP
            json_data = json.loads(json_result)
            primer_elemento_sql = json_data[0]
            estadoSQL = primer_elemento_sql.get('estatus')
            mensajeSQL = primer_elemento_sql.get('mensaje')
            password_hashSQL = primer_elemento_sql.get('password_hash')

            #Retornamos 
            return {
                "estatus": estadoSQL,
                "mensaje": mensajeSQL,
                "password_hash": password_hashSQL
            }
        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en obtener_cliente_login:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL - obtener_cliente_login")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en obtener_cliente_login: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - obtener_cliente_login")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - obtener_cliente_login")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - obtener_cliente_login")      
    
    # Actualizar Pass de usuario
    @staticmethod
    def actualizar_password(data):
        try:
            LOG.info("## actualizar_password ##")
            # Obtenemos valores 
            cod_cliente = data["cod_cliente"].strip()
            correo = data["correo_cliente"].strip()
            actual_password = data["actual_password"]
            nueva_password = data["nueva_password"]

            #Consultamos usuario y validamos
            result_obtener = UsuariosService.obtener_cliente_login(cod_cliente)
            estatus_result = result_obtener["estatus"]
            mensaje_result = result_obtener["mensaje"]
            password_hash_result = result_obtener["password_hash"]

            if estatus_result != STATUS_CODE_200:
                LOG.info(f"{mensaje_result}: {cod_cliente}")
                return api_response(STATUS_CODE_401,{},LOGIN_FAILED,mensaje_result)

            #Valida si pass es correcto
            es_pass_valido = check_password(password_hash_result, actual_password)

            if not es_pass_valido:
                LOG.info(f"Contraseña incorrecta para el cliente: {cod_cliente}")
                return api_response(STATUS_CODE_401,{},LOGIN_FAILED,CREDENCIALES_FALLIDAS)

            #Hash a nva password
            password_hash = set_password(nueva_password)

            #Envio de datos
            actualizar_result = UsuariosModel.actualizar_password(cod_cliente,correo,password_hash)

            # Convertimos valores obtenidos
            columns = actualizar_result.keys()
            rows = actualizar_result.fetchall()
            df_result = pd.DataFrame(rows, columns=columns)
            json_result = df_result.to_json(orient="records")
            
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
                f"Err al realizar la sentencia en actualizar_password:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en actualizar_password: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - actualizar_password")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - actualizar_password")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - actualizar_password")   


    # Actualizar Permiso de acceso a sistema
    @staticmethod
    def actualizar_permiso_sic(data):
        try:
            LOG.info("## actualizar_permiso_app ##")
            # Obtenemos valores 
            usuario = data["usuario"].strip()
            flag_permiso = data["flag_permiso"]

            #Envio de datos
            actualizar_permiso_result = UsuariosModel.actualizar_permiso_app(usuario,flag_permiso)

            # Convertimos valores obtenidos
            columns = actualizar_permiso_result.keys()
            rows = actualizar_permiso_result.fetchall()
            df_result = pd.DataFrame(rows, columns=columns)
            json_result = df_result.to_json(orient="records")
            
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
                f"Err al realizar la sentencia en actualizar_permiso_app:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en actualizar_permiso_app: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - actualizar_permiso_app")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - actualizar_permiso_app")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - actualizar_permiso_app")           

    @staticmethod
    def listado_usuarios(data):
        try:
            LOG.info("## listado_usuarios ##")
            listado_result = UsuariosModel.obtener_usuarios()

            # Convertimos valores obtenidos
            columns = listado_result.keys()
            rows = listado_result.fetchall()

            # Validamos resultado
            if columns is None or len(rows) == 0:
                LOG.info(f"GET /listado-usuarios")
                return api_response(STATUS_CODE_404, [],ERROR,ERROR_EMPTY)

            df_result = pd.DataFrame(rows, columns=columns)
            total_registros = len(df_result) 

            # Limpiar t_body antes de asignar nuevos valores
            t_body = []

            # Convertimos las filas de datos en una lista de diccionarios
            t_body = df_result.to_dict(orient="records")
            msj = f"{total_registros} Empleado(s) encontrado(s)"
            
            return api_response(STATUS_CODE_200,t_body,SUCCESS,msj)


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