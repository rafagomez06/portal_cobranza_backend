import os
from app.models.UsuariosModel import UsuariosModel
from app.services.CorreoService import CorreoService
from flask import request
from flask_jwt_extended import create_access_token,decode_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import timedelta
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
            correo = data["correo"].strip().lower()

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
            # Obtenemos valores 
            cod_cliente = data["cod_cliente"].strip()
            correo = data["correo"].strip().lower()
            password = data["password"]

            #Consultamos usuario y validamos
            result_obtener = UsuariosService.obtener_pass_cliente_login(cod_cliente)
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
            moneda_cliente = primer_elemento_sql.get('moneda')

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
                    "moneda_cliente":moneda_cliente
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
    def obtener_pass_cliente_login(cliente):
        try:
            LOG.info("## obtener_pass_cliente_login ##")

            # Obtenemos valores 
            result = UsuariosModel.obtener_pass_cliente_login(cliente)

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
                f"Err al realizar la sentencia en obtener_pass_cliente_login:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL - obtener_pass_cliente_login")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en obtener_pass_cliente_login: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - obtener_pass_cliente_login")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - obtener_pass_cliente_login")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - obtener_pass_cliente_login")      

    # Valida correo este vigente para envio de reinicio pass
    @staticmethod
    def validar_correo_cliente(correo_cliente):
        try:
            LOG.info("## validar_correo_cliente ##")

            # Obtenemos valores 
            result = UsuariosModel.validar_correo_cliente(correo_cliente)

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

            #Retornamos 
            return {
                "estatus": estadoSQL,
                "mensaje": mensajeSQL
            }
        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en validar_correo_cliente:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL - validar_correo_cliente")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en validar_correo_cliente: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - validar_correo_cliente")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - validar_correo_cliente")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - validar_correo_cliente")  

    # Envio de correo de pass olvidada
    @staticmethod
    def solicitar_reiniciar_password_mail(data):
        try:
            LOG.info("## solicitar_reiniciar_password_mail ##")
            # Obtenemos Correo
            correo_cliente = data["correo"].strip().lower()

            # Consultamos correo sea valido y activo
            result_obtener = UsuariosService.validar_correo_cliente(correo_cliente)
            estatus_result = result_obtener["estatus"]
            mensaje_result = result_obtener["mensaje"]

            # Retornamos 200 para seguridad, mensaje generico.
            if estatus_result != STATUS_CODE_200:
                LOG.info(f"{mensaje_result}: {correo_cliente}")
                return api_response(STATUS_CODE_200,{},RESET_PASS_FAILED,CORREO_ENVIADO)

            # Generamos JWT para el reinicio de contraseña con vigencia de 5 min
            # Puedes guardar claims adicionales si requieres verificar el propósito del token
            reset_token = create_access_token(
                identity=correo_cliente,
                expires_delta=timedelta(minutes=5),
                additional_claims={"type": "password_reset"}
            )

            # Obtenemos la ruta de variable de entorno
            URL_FRONT = os.getenv("COBRANZA_FLASK_SERVER_FRONT")
            # Construir la URL del Frontend con el token
            frontend_url = URL_FRONT # O toma la variable desde la configuración
            action_url = f"{frontend_url}/actualizar-password?token={reset_token}"

            # Parametros para rendereizar en el template del correo
            datos_correo = {
                "para": correo_cliente,
                "asunto": ASUNTO_MAIL,
                "template_name": TEMPLATE_URL,
                "template_data": {
                    "nombre": correo_cliente,
                    "nombre_cuenta": NOMBRE_SISTEMA,
                    "nombre_empresa": NOMBRE_EMPRESA,
                    "logo_url": LOGO_URL,
                    "action_url": action_url,
                    "correo_soporte": CORREO_SOPORTE,
                    "direccion_empresa": DIRECCION_EMPRESA,
                    "ciudad_estado_cp": CIUDAD_EMRESA
                }
            }
            #Envio de correo para reinicio de contraseña
            CorreoService.enviar_correo(datos_correo)

            return api_response(STATUS_CODE_200,{},CORREO_ENVIADO,CORREO_ENVIADO)

        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en solicitar_reiniciar_password_mail:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en solicitar_reiniciar_password_mail: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - solicitar_reiniciar_password_mail")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos - solicitar_reiniciar_password_mail")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - solicitar_reiniciar_password_mail")   

    @staticmethod
    def actualizar_password_token(data):
        try:
            token = data.get("token")
            nueva_password = data.get("nueva_password")

            if not token or not nueva_password:
                return api_response(STATUS_CODE_400, {}, ERROR, PARAMS_INCOMPLETOS)

            # Decodificamos y validamos el token
            try:
                decoded_token = decode_token(token)
            except ExpiredSignatureError:
                return api_response(STATUS_CODE_400, {}, ERROR, ENLACE_EXPIRADO)
            except InvalidTokenError:
                return api_response(STATUS_CODE_400, {}, ERROR, ENLACE_INVALIDO)

            # Verificar el tipo de claim 
            claims = decoded_token.get("sub", {}) # O en 'type' si usaste additional_claims
            correo_usuario = decoded_token.get("sub")  # Contiene la identidad especificada al crear el token
            
            if decoded_token.get("type") != "password_reset":
                return api_response(STATUS_CODE_400, {}, ERROR, "Token no autorizado para esta acción")

            #  Encriptamos y actualizamos la contraseña en la bd
            hashed_password = set_password(nueva_password)

            #Enviarmos parametros
            data={
                "correo_usuario":correo_usuario,
                "hashed_password": hashed_password
            }
            # actualizacion en BD de la nueva Pass
            result_bd = UsuariosService.actualizar_password_bd(data)

            # Convertimos valores obtenidos
            if result_bd != STATUS_CODE_200:
                return api_response(STATUS_CODE_400,{},ERROR,ERROR_GENERICO)

            return api_response(STATUS_CODE_200, {}, SUCCESS, PASSWORD_SUCCESS)

        except Exception as e:
            LOG.error(f"Error al cambiar la contraseña: {str(e)}")
            raise UnexpectedError("Ocurrió un error al intentar cambiar la contraseña.")

    @staticmethod
    def actualizar_password_bd(data):
        try:
            LOG.info("## actualizar_password_bd ##")
            # Obtenemos valores 
            correo_usuario = data["correo_usuario"].strip()
            nueva_pass = data["hashed_password"].strip()

            #Envio de datos
            registrar_result = UsuariosModel.actualizar_password(correo_usuario,nueva_pass)

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
                return STATUS_CODE_400
            
            #Commit y Retorno de datos
            ConnectionDb.alchemy_db.session.commit()
            return STATUS_CODE_200

        except exc.StatementError as sta_err:
            error_trace = traceback.format_exc()
            LOG.error(
                f"Err al realizar la sentencia en actualizar_password_bd:{str(sta_err)} [{error_trace}]")
            raise DatabaseError("Err al realizar la sentencia SQL")
        except exc.SQLAlchemyError as e: 
            LOG.error(f"DB error en actualizar_password_bd: {str(e)}")
            raise DatabaseError("Error al consultar la base de datos - actualizar_password_bd")
        except ValueError as e: 
            LOG.warning(f"Parámetro inválido: {str(e)}")
            raise UnexpectedError("Parámetros de búsqueda inválidos")
        except Exception as e:  
            error_trace = traceback.format_exc()
            LOG.error(f"Error inesperado: {str(e)} | Trace: {error_trace}")
            raise UnexpectedError("Ocurrió un error inesperado - actualizar_password_bd") 


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