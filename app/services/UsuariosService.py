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
            id_empleado = data["id_empleado"]
            id_empresa = data["id_empresa"]
            usuario_checador = data["usuario_checador"].strip()
            nombre = data["nombre"].strip()
            apellido_paterno = data["apellido_paterno"].strip()
            apellido_materno = data["apellido_materno"].strip()
            correo = data["correo"].strip()
            usuario_creacion = data["usuario_creacion"].strip()

            #password_hash = set_password(password)
            #Envio de datos
            registrar_result = UsuariosModel.registrar_usuario(id_empleado,
                                                            id_empresa,usuario_checador,nombre
                                                            ,apellido_paterno
                                                            ,apellido_materno,correo,usuario_creacion)

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
            usuario = data["usuario"].strip()
            password = data["password"]

            #Consultamos usuario y validamos
            result_obtener = UsuariosService.obtener_usuario_login(usuario)
            estatus_result = result_obtener["estatus"]
            mensaje_result = result_obtener["mensaje"]
            password_hash_result = result_obtener["password_hash"]

            if estatus_result != STATUS_CODE_200:
                LOG.info(f"{mensaje_result}: {usuario}")
                return api_response(STATUS_CODE_401,{},LOGIN_FAILED,mensaje_result)

            #Valida si pass es correcto
            es_pass_valido = check_password(password_hash_result, password)

            if not es_pass_valido:
                LOG.info(f"Contraseña incorrecta para el usuario: {usuario}")
                return api_response(STATUS_CODE_401,{},LOGIN_FAILED,CREDENCIALES_FALLIDAS)
            
            #Validamos login
            valida_result = UsuariosModel.validar_login(usuario,password_hash_result)

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
            nombre_usuarioSQL = primer_elemento_sql.get('nombre_usuario')
            correo_usuarioSQL = primer_elemento_sql.get('correo')
            id_empleadoSQL = primer_elemento_sql.get('id_empleado')

            #Obtenemos datos jornada
            dia_semanaSQL = primer_elemento_sql.get('dia_semana')
            clave_turnoSQL = primer_elemento_sql.get('clave_turno')
            festivoSQL = primer_elemento_sql.get("festivo")
            es_laboralSQL = primer_elemento_sql.get("es_laboral")
            hora_inicioSQL = primer_elemento_sql.get('hora_inicio')
            hora_finSQL = primer_elemento_sql.get('hora_fin')


            # si SP falla se retorna su respuesta
            if estadoSQL != STATUS_CODE_200:
                LOG.info(f"Error: {mensajeSQL} ")
                # ConnectionDb.alchemy_db.session.rollback()
                return api_response(STATUS_CODE_400,{},LOGIN_FAILED,mensajeSQL)
            
            # Generamos token unico
            token = create_access_token(identity=str(usuario))

            t_body = []

            # Convertimos las filas de datos en una lista de diccionarios
            t_body = {
                    "token": token,
                    "nombre_usuario":nombre_usuarioSQL,
                    "correo_usuario":correo_usuarioSQL,
                    "id_empleado":id_empleadoSQL,
                    "usuario": usuario,
                    "jornada":{
                            "dia_semana": dia_semanaSQL,
                            "clave_turno": clave_turnoSQL,
                            "festivo": festivoSQL,
                            "es_laboral": es_laboralSQL,
                            "hora_inicio": hora_inicioSQL,
                            "hora_fin": hora_finSQL,
                        }
                        }

            #Commit y Retorno de datos
            # return api_response(STATUS_CODE_200,json_data,SUCCESS,mensajeSQL)
            return api_response(STATUS_CODE_200,t_body ,SUCCESS,LOGIN_SUCCESS)

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

    # Obtiene la pass de usuario hasheada (encriptada)
    @staticmethod
    def obtener_usuario_login(usuario):
        try:
            LOG.info("## obtener_usuario_login ##")

            # Obtenemos valores 
            result = UsuariosModel.obtener_usuario_login(usuario)

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
    
    # Actualizar Pass de usuario
    @staticmethod
    def actualizar_password(data):
        try:
            LOG.info("## actualizar_password ##")
            # Obtenemos valores 
            usuario = data["usuario"].strip()
            nueva_password = data["nueva_password"]

            password_hash = set_password(nueva_password)

            #Envio de datos
            actualizar_result = UsuariosModel.actualizar_password(usuario,password_hash)

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


    # Actualizar Permiso a uso de la app
    @staticmethod
    def actualizar_permiso_app(data):
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