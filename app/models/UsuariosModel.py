from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import insert, text

LOG = logger()
sql_connection = ConnectionDb.alchemy_db

## Modelos de tablas de catalogos

class UsuariosModel(sql_connection.Model):
    __tablename__ = 'UsuariosModel'

    id_UsuariosModel = sql_connection.Column(sql_connection.Integer, primary_key=True)
    nombre = sql_connection.Column(sql_connection.String(100), nullable=False)

    def __init__(self, id_UsuariosModel, nombre=None) -> None:
        self.id_UsuariosModel = id_UsuariosModel
        self.nombre = nombre

    @staticmethod
    def obtener_usuarios():
        sql = text(f"EXEC sp_ObtenerListadoUsuariosChecadorApp;")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def validar_login(usuario,password_hash):
        sql = text(f"EXEC sp_ValidarUsuariosChecador @UsuarioChecador='{usuario}',@Password='{password_hash}';")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def actualizar_password(usuario,password_hash):
        sql = text(f"EXEC sp_ActualizarPasswordUsuario @UsuarioChecador='{usuario}',@Password='{password_hash}';")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result

    @staticmethod
    def actualizar_permiso_app(usuario,flag_permiso):
        sql = text(f"EXEC sp_ActualizarPermisoAPP @UsuarioChecador='{usuario}',@FlagPermiso={flag_permiso};")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def obtener_usuario_login(usuario):
        sql = text(f"EXEC sp_ObtenerUsuarioLogin @UsuarioChecador='{usuario}';")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def registrar_usuario(id_empleado, id_empresa,usuario_checador,nombre,apellido_paterno,apellido_materno,correo,usuario_creacion):
        sql = text(f"EXEC sp_RegistrarUsuarioChecadorApp @IdEmpleado={id_empleado},@IdEmpresa={id_empresa},"
                f"@UsuarioChecador='{usuario_checador}',@NombreUsuario='{nombre}',@ApellidoPaterno='{apellido_paterno}',"
                f"@ApellidoMaterno='{apellido_materno}',@Correo='{correo}',@UsuarioCreacion='{usuario_creacion}';")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result


    def roll_back(self):
        sql_connection.session.rollback(self)

